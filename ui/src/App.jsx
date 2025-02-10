import { ArrowPathIcon, PauseIcon } from '@heroicons/react/24/solid'; // Versión v2

import { useEffect, useState } from 'react'

function App() {
  const [agents, setAgents] = useState(0)

  /**
   * Fetch agents from Elaiza API
   */
  const handleFecthAgents = async () => {
    try {
      const response = await fetch('http://localhost:3000/agents')
      const data = await response.json()
      /** Example of data
         {
              "agents": [
                  {
                      "id": "e0e10e6f-ff2b-0d4c-8011-1fc1eee7cb32",
                      "name": "trump",
                      "clients": [
                          "twitter"
                      ]
                  }
              ]
          }
       */
      setAgents(data.agents)

    } catch (error) {
      setAgents(false)
    }
  }

  const handleStopAgent = async (agentId) => {
    try {
      const response = await fetch(`http://localhost:3000/agents/${agentId}/stop`, {
        method: 'POST'
      })
      const data = await response.json()
      console.log(data)
    } catch (error) {
      console.log(error)
    }
  }

useEffect(() => {
  handleFecthAgents()
}, [])

return (
  <>
    <main className="grid grid-rows-3 place-items-center h-screen w-full">
      <h1 className="h-fit text-3xl font-bold">Eliza AIM</h1>
      <section className="w-3/5 mx-auto flex flex-col gap-4 mb-[15%]">
        <div className="flex justify-between">
          <div></div>
          <h2 className="text-center text-xl font-bold content-center">Agents</h2>
          <button onClick={handleFecthAgents} className="bg-orange-500
                       hover:bg-orange-700 text-white font-bold py-2 px-2 rounded-full cursor-pointer">
            <ArrowPathIcon className="h-6 w-6 text-white" />
          </button>
        </div>
        <hr />
        <ul>
          {agents && agents.map(agent => (
            <li key={agent.id}>
              <h2 className="text-lg font-semibold ml-2">- {agent.name}</h2>
              <ul className="ml-4">
                {agent.clients.map(client => (
                  <li className="flex justify-between" key={client}>
                    <span>• {client}</span>
                    <div>
                      <button className="bg-orange-500
                       hover:bg-orange-700 text-white font-bold py-1 px-1 rounded-full cursor-pointer">
                        <PauseIcon className="h-2 w-2 text-white"
                          onClick={() => handleStopAgent(agent.id)}
                        />
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      </section>
      <img className="fixed -bottom-10 -left-10" src="/eliza.avif" alt="" />
    </main>
  </>
)
}

export default App
