"use client";

import { useEffect, useState } from "react";
import { fetchAgents, createAgent, updateAgent, deleteAgent } from "@/lib/api";
import { Users, Plus, Cpu, Shield, Wrench, Edit2, Trash2, Globe, MessageSquare, Brain, ShieldCheck, Clock, Layers } from "lucide-react";

export default function AgentsPage() {
  const [agents, setAgents] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [editingAgent, setEditingAgent] = useState<any>(null);
  const [activeTab, setActiveTab] = useState("basic");
  
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    role: "",
    system_prompt: "",
    model_name: "llama-3.1-8b-instant",
    tools: [] as string[],
    channels: [] as string[],
    memory_enabled: true,
    schedule: "",
    interaction_rules: "",
    guardrails: ""
  });

  const loadAgents = () => {
    fetchAgents().then(setAgents).catch(console.error);
  };

  useEffect(() => {
    loadAgents();
  }, []);

  const openEditModal = (agent: any) => {
    setEditingAgent(agent);
    setFormData({
      name: agent.name,
      description: agent.description,
      role: agent.role,
      system_prompt: agent.system_prompt,
      model_name: agent.model_name || "llama-3.1-8b-instant",
      tools: agent.tools || [],
      channels: agent.channels || [],
      memory_enabled: agent.memory_enabled !== false,
      schedule: agent.schedule || "",
      interaction_rules: agent.interaction_rules || "",
      guardrails: agent.guardrails || ""
    });
    setActiveTab("basic");
    setShowModal(true);
  };

  const openCreateModal = () => {
    setEditingAgent(null);
    setFormData({
      name: "",
      description: "",
      role: "",
      system_prompt: "",
      model_name: "llama-3.1-8b-instant",
      tools: [],
      channels: [],
      memory_enabled: true,
      schedule: "",
      interaction_rules: "",
      guardrails: ""
    });
    setActiveTab("basic");
    setShowModal(true);
  };

  const handleDelete = async (id: number) => {
    if (window.confirm("Are you sure you want to delete this agent?")) {
      await deleteAgent(id);
      loadAgents();
    }
  };

  const handleSubmit = async (e: any) => {
    e.preventDefault();
    try {
      if (editingAgent) {
        await updateAgent(editingAgent.id, formData);
      } else {
        await createAgent(formData);
      }
      setShowModal(false);
      loadAgents();
    } catch (err) {
      console.error(err);
      alert("Failed to save agent");
    }
  };

  const toggleTool = (tool: string) => {
    setFormData(prev => ({
      ...prev,
      tools: prev.tools.includes(tool) 
        ? prev.tools.filter(t => t !== tool)
        : [...prev.tools, tool]
    }));
  };

  const toggleChannel = (channel: string) => {
    setFormData(prev => ({
      ...prev,
      channels: prev.channels.includes(channel) 
        ? prev.channels.filter(c => c !== channel)
        : [...prev.channels, channel]
    }));
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <header className="flex justify-between items-end">
        <div>
          <h1 className="text-4xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-pink-400 via-purple-400 to-indigo-400 mb-2">
            Agent Fleet
          </h1>
          <p className="text-slate-400 text-lg">Manage and configure your autonomous AI workforce.</p>
        </div>
        <button 
          onClick={openCreateModal}
          className="flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-3 rounded-xl font-medium transition-all shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/40"
        >
          <Plus className="w-5 h-5" />
          <span>New Agent</span>
        </button>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {agents.map((agent: any) => (
          <div key={agent.id} className="glass-card p-6 flex flex-col group hover:-translate-y-1 transition-transform duration-300">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-slate-800/50 rounded-xl group-hover:bg-indigo-500/20 transition-colors">
                <Cpu className="w-6 h-6 text-indigo-400" />
              </div>
              <div className="flex items-center space-x-2">
                <button 
                  onClick={() => openEditModal(agent)}
                  className="p-2 text-slate-400 hover:text-indigo-400 hover:bg-indigo-400/10 rounded-lg transition-colors"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
                <button 
                  onClick={() => handleDelete(agent.id)}
                  className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
                <span className="px-3 py-1 bg-slate-800 rounded-full text-xs font-mono text-slate-400 border border-slate-700">
                  {agent.model_name || "llama-3.1-8b-instant"}
                </span>
              </div>
            </div>
            <h3 className="text-xl font-bold text-white mb-1">{agent.name}</h3>
            <p className="text-slate-400 text-sm mb-4 flex-1 line-clamp-2">{agent.description}</p>
            
            <div className="space-y-3 mt-auto pt-4 border-t border-slate-800">
              <div className="flex items-center text-sm text-slate-300">
                <Shield className="w-4 h-4 mr-2 text-slate-500" />
                <span className="font-medium text-slate-400 mr-2">Role:</span> {agent.role}
              </div>
              <div className="flex items-center text-sm text-slate-300">
                <Wrench className="w-4 h-4 mr-2 text-slate-500" />
                <span className="font-medium text-slate-400 mr-2">Tools:</span> 
                {agent.tools && agent.tools.length > 0 ? agent.tools.join(", ") : "None"}
              </div>
              {agent.channels && agent.channels.length > 0 && (
                <div className="flex items-center text-sm text-slate-300">
                  <MessageSquare className="w-4 h-4 mr-2 text-slate-500" />
                  <span className="font-medium text-slate-400 mr-2">Channels:</span> 
                  {agent.channels.join(", ")}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in">
          <div className="glass-card w-full max-w-2xl p-8 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">{editingAgent ? "Edit Agent" : "Deploy New Agent"}</h2>
              <div className="flex bg-slate-800/50 p-1 rounded-xl">
                <button 
                  onClick={() => setActiveTab("basic")}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${activeTab === "basic" ? "bg-indigo-600 text-white shadow-lg" : "text-slate-400 hover:text-white"}`}
                >
                  Basic
                </button>
                <button 
                  onClick={() => setActiveTab("advanced")}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${activeTab === "advanced" ? "bg-indigo-600 text-white shadow-lg" : "text-slate-400 hover:text-white"}`}
                >
                  Advanced
                </button>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {activeTab === "basic" ? (
                <div className="space-y-6 animate-in slide-in-from-left-4 duration-300">
                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-slate-400 mb-2">Agent Name</label>
                      <input required type="text" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 focus:outline-none focus:border-indigo-500 transition-colors text-white" placeholder="e.g. Data Analyst" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-400 mb-2">Role</label>
                      <input required type="text" value={formData.role} onChange={e => setFormData({...formData, role: e.target.value})} className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 focus:outline-none focus:border-indigo-500 transition-colors text-white" placeholder="e.g. Analyzer" />
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-2">Description</label>
                    <input required type="text" value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 focus:outline-none focus:border-indigo-500 transition-colors text-white" />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-2">Model</label>
                    <select 
                      value={formData.model_name} 
                      onChange={e => setFormData({...formData, model_name: e.target.value})}
                      className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 focus:outline-none focus:border-indigo-500 transition-colors text-white appearance-none"
                    >
                      <option value="llama-3.1-8b-instant">Llama 3.1 8B (Fast)</option>
                      <option value="llama-3.3-70b-versatile">Llama 3.3 70B (Versatile)</option>
                      <option value="llama3-70b-8192">Llama 3 70B (Stable)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-2">System Prompt</label>
                    <textarea required rows={4} value={formData.system_prompt} onChange={e => setFormData({...formData, system_prompt: e.target.value})} className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 focus:outline-none focus:border-indigo-500 transition-colors text-white" placeholder="You are a helpful assistant..."></textarea>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-3">Capabilities (Tools)</label>
                    <div className="flex flex-wrap gap-3">
                      {["web_search", "calculator", "http_request", "weather"].map(tool => (
                        <button
                          key={tool}
                          type="button"
                          onClick={() => toggleTool(tool)}
                          className={`px-4 py-2 rounded-xl text-sm font-medium transition-all border ${
                            formData.tools.includes(tool) 
                              ? 'bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-500/20' 
                              : 'bg-slate-900 border-slate-700 text-slate-400 hover:border-slate-500'
                          }`}
                        >
                          {tool}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-6 animate-in slide-in-from-right-4 duration-300">
                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-3">External Channels</label>
                    <div className="flex flex-wrap gap-3">
                      {["Telegram"].map(channel => (
                        <button
                          key={channel}
                          type="button"
                          onClick={() => toggleChannel(channel)}
                          className={`px-4 py-2 rounded-xl text-sm font-medium transition-all border ${
                            formData.channels.includes(channel) 
                              ? 'bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-500/20' 
                              : 'bg-slate-900 border-slate-700 text-slate-400 hover:border-slate-500'
                          }`}
                        >
                          {channel}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <label className="flex items-center text-sm font-medium text-slate-400 mb-2">
                        <Brain className="w-4 h-4 mr-2 text-indigo-400" />
                        Memory Storage
                      </label>
                      <div className="flex items-center h-12 px-4 bg-slate-900 border border-slate-700 rounded-xl">
                        <input 
                          type="checkbox" 
                          checked={formData.memory_enabled}
                          onChange={e => setFormData({...formData, memory_enabled: e.target.checked})}
                          className="w-5 h-5 rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-indigo-500"
                        />
                        <span className="ml-3 text-slate-300 text-sm">Persistent Memory</span>
                      </div>
                    </div>
                    <div>
                      <label className="flex items-center text-sm font-medium text-slate-400 mb-2">
                        <Clock className="w-4 h-4 mr-2 text-indigo-400" />
                        Schedule (Cron)
                      </label>
                      <input 
                        type="text" 
                        value={formData.schedule} 
                        onChange={e => setFormData({...formData, schedule: e.target.value})} 
                        className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 focus:outline-none focus:border-indigo-500 transition-colors text-white" 
                        placeholder="e.g. 0 9 * * 1-5"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="flex items-center text-sm font-medium text-slate-400 mb-2">
                      <Layers className="w-4 h-4 mr-2 text-indigo-400" />
                      Interaction Rules
                    </label>
                    <textarea 
                      rows={3} 
                      value={formData.interaction_rules} 
                      onChange={e => setFormData({...formData, interaction_rules: e.target.value})} 
                      className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 focus:outline-none focus:border-indigo-500 transition-colors text-white" 
                      placeholder="Define how the agent should interact with other agents or users..."
                    ></textarea>
                  </div>

                  <div>
                    <label className="flex items-center text-sm font-medium text-slate-400 mb-2">
                      <ShieldCheck className="w-4 h-4 mr-2 text-indigo-400" />
                      Guardrails
                    </label>
                    <textarea 
                      rows={3} 
                      value={formData.guardrails} 
                      onChange={e => setFormData({...formData, guardrails: e.target.value})} 
                      className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 focus:outline-none focus:border-indigo-500 transition-colors text-white" 
                      placeholder="Specify safety boundaries, content restrictions, etc..."
                    ></textarea>
                  </div>
                </div>
              )}

              <div className="flex justify-end space-x-4 pt-4 border-t border-slate-800">
                <button type="button" onClick={() => setShowModal(false)} className="px-6 py-3 text-slate-400 hover:text-white font-medium transition-colors">
                  Cancel
                </button>
                <button type="submit" className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white px-8 py-3 rounded-xl font-bold shadow-lg hover:opacity-90 transition-opacity">
                  {editingAgent ? "Update Agent" : "Initialize Agent"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
