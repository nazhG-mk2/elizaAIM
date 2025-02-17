from pyhypercycle_aim import SimpleServer, aim_uri, JSONResponseCORS, HTMLResponseCORS  # type: ignore
from http.server import BaseHTTPRequestHandler, HTTPServer
import aiofiles
import asyncio
import httpx # type: ignore
import json
import time
import os

PORT = int(os.environ.get("PORT", 8000))

SUBSCRIPTION_FILE = "./container_mount/subscription.json"

class ElizaBot(SimpleServer):
    """
        health(request):
            Returns the health status of the service.
        index(request):
            Returns the UI for the service. #TODO
        agents(request):
            Returns the list of agents.
        stop_agent(request):
            Stops an agent.
        start_agent(request):
            Starts an agent.
        example_agent(request):
            Returns an example agent.
        set_account(request):
            Sets the credentials for the twitter connection.
        set_api_key(request):
            Sets the API key for the GROQ connection.
        startup_job():
            Starts the subscription check loop.
        subscribe(request):
            Subscribes in order to be able to set an agent.
            Note: 
            Q. why subscription? 
            A. may be user will want to change the agent knowledge o behavior of an agents, so he will need to stop the agent and restart it with new information.
        check_subscription():
            Checks if the subscription is still valid.
        subscription(request):
            Returns the current subscription status.
        subscription_check_loop():
            Periodically checks the subscription status and stops agents if the subscription is over.
    """

    manifest = {
        "name": "ElizaBot",
        "short_name": "eliza",
        "version": "0.1",
        "author": "nazhG"
    }
    
    # Health check
    @aim_uri(uri="/health", methods=["GET"],
        endpoint_manifest = {
            "documentation": "Returns the health status of the service",
            "output": {"status":"<updated|error>"},
    })
    async def health(self, request):
        rval={"status": "Everything is fine!"}
        return JSONResponseCORS(rval, costs=[])
    
    # UI
    @aim_uri(uri="/", methods=["GET"],
            endpoint_manifest = {
                "documentation": "Returns ui for the service",
                "output": "html",
        })
    async def index(self, request):
        with open("./ui/dist/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponseCORS(html_content)
    
    # Get Agents
    @aim_uri(uri="/agents", methods=["GET"],
        endpoint_manifest = {
            "documentation": "Returns the list of agents",
            "output": "json",
    })
    async def agents(self, request):
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:3000/agents")
            agents = response.json()
        return JSONResponseCORS(agents, costs=[])
    
    # Stop an Agent
    @aim_uri(uri="/agents/stop", methods=["POST"],
        endpoint_manifest = {
            "documentation": "Stops an agent",
            "input_body": {"agent_id": "<String>"},
            "output": {"status":"<updated|error>"},
    })
    async def stop_agent(self, request):
        body = await request.json()
        agent_id = body.get("agent_id")
        
        if not agent_id:
            return JSONResponseCORS({"status": "error", "message": "agent_id is required"}, costs=[])
        
        async with httpx.AsyncClient() as client:
            response = await client.post(f"http://localhost:3000/agents/{agent_id}/stop")
            status = response.json()
        return JSONResponseCORS(status, costs=[])
    
    # Start an Agent
    @aim_uri(uri="/agents/start", methods=["POST"],
        endpoint_manifest = {
            "documentation": "Starts an agent",
            "input_body": {"character": "<JSON>"},
            "output": {"status":"<updated|error>"},
    })
    async def start_agent(self, request):
        body = await request.json()
        character = body.get("character")
        
        agent_id = body.get("agent_id")
        
        if not agent_id:
            return JSONResponseCORS({"status": "error", "message": "agent_id is required"}, costs=[])
        
        if not character:
            return JSONResponseCORS({"status": "error", "message": "character is required"}, costs=[])
        
        # Check if subscription is over
        subscription = self.check_subscription()
        if not subscription:
            return JSONResponseCORS({"status": "error", "message": "Subscription is over"}, costs=[])
        
        async with httpx.AsyncClient() as client:
            response = await client.post("http://localhost:3000/agents/{agent_id}/set", json=character)
            status = response.json()
            print(response.status_code, response.text)
        return JSONResponseCORS(status, costs=[])
    
    # Returns eliza.character.json file as an example agent
    @aim_uri(uri="/agents/example", methods=["GET"],
        endpoint_manifest = {
            "documentation": "Returns an example agent",
            "output": "json",
    })
    async def example_agent(self, request):
        with open("./eliza.character.json", "r", encoding="utf-8") as f:
            agent = f.read()
        return JSONResponseCORS(agent, costs=[])

    # Initialize the subscription check loop
    def startup_job(self):
        asyncio.create_task(self.subscription_check_loop())
        
    # Subscribe to be able to set an agent
    @aim_uri(uri="/subscribe", methods=["POST"],
        endpoint_manifest = {
            "documentation": "Subscribe to the service",
            "output": {"status":"<updated|error>"},
    })
    async def subscribe(self, request):
        # Number of months to subscribe
        body = await request.json()
        months = body.get("months", 1)
        user_address = self.get_user_address(request)
        
        async with self.lock: # Lock the subscription file
            try:
                async with aiofiles.open(SUBSCRIPTION_FILE, "r") as f:
                    content = await f.read()
                    subscription = json.loads(content) if content else {}
            except (FileNotFoundError, json.JSONDecodeError):
                subscription = {}

            subscription[user_address] = subscription.get(user_address, time.time()) + 60*60*24*30*months
            costs = [{"currency": "ProcessingUnits","used": 1*months}]

            async with aiofiles.open(SUBSCRIPTION_FILE, "w") as f:
                await f.write(json.dumps(subscription))
            
        return JSONResponseCORS({"status": "updated", "end": subscription[user_address]}, costs)
        
    # Check Subscription
    @aim_uri(uri="/subscription", methods=["GET"],
        endpoint_manifest = {
            "documentation": "Sets the subscription",
            "input_body": {"subscription": "<JSON>"},
            "output": {"status":"<updated|error>"},
            "example_call": {
                "subscription": {
                    "end": 1630000000
                }
            }
    })
    async def subscription(self, request):
        subscription = self.check_subscription()
        if not subscription:
            return JSONResponseCORS({"status": "error", "message": "Subscription is over"}, costs=[])
        return JSONResponseCORS(subscription, costs=[])

    # Check if user.address is subscribed.        
    def check_subscription(self, request):
        user_address = self.get_user_address(request)

        try:
            with open(SUBSCRIPTION_FILE, "r") as f:
                content = f.read()
                subscription = json.loads(content) if content else {}
        except (FileNotFoundError, json.JSONDecodeError):
            subscription = {}

        expiry = subscription.get(user_address, 0)
        return expiry > time.time()
    
    # Check Subscription every hour
    async def subscription_check_loop(self):
        print("Subscription check loop started")
        # Create subscription file if not exists
        if not os.path.exists(SUBSCRIPTION_FILE):
            with open(SUBSCRIPTION_FILE, "w") as f:
                f.write("{}")
        # Main loop
        while True:
            try: # Check if the subscription time is over
                if not self.check_subscription():
                    # Get all agents
                    agents = await self.agents()
                    for agent in agents.get("agents"):
                        await self.stop_agent({"agent_id": agent.get("id")})
            except Exception as e:
                print("Error in subscription check loop")
                print(e)                
                
            await asyncio.sleep(60*60) # 1 hour
        
def main():
    print("ElizaBot: hi!")
    app = ElizaBot()
    app.run(uvicorn_kwargs={"port": PORT, "host": "0.0.0.0"})
    print("ElizaBot: bye!")

if __name__ == "__main__":
    main()
