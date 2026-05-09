"use client";

import { useEffect, useState } from "react";
import { fetchWorkflows, fetchRecentExecutions, clearExecutions, fetchExecution } from "@/lib/api";
import { Activity, CheckCircle2, Clock, PlayCircle, Zap, Trash2, X, ChevronRight, Loader2 } from "lucide-react";

export default function Dashboard() {
  const [workflows, setWorkflows] = useState([]);
  const [executions, setExecutions] = useState([]);
  const [selectedExecution, setSelectedExecution] = useState<any>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

  const loadData = () => {
    fetchWorkflows().then(setWorkflows).catch(console.error);
    fetchRecentExecutions().then(setExecutions).catch(console.error);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleClear = async () => {
    if (confirm("Are you sure you want to clear all execution history?")) {
      await clearExecutions();
      loadData();
    }
  };

  const openDetails = async (id: number) => {
    setLoadingDetails(true);
    try {
      const details = await fetchExecution(id);
      setSelectedExecution(details);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingDetails(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <header>
        <h1 className="text-4xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 mb-2">
          Platform Overview
        </h1>
        <p className="text-slate-400 text-lg">Monitor your autonomous agent workflows in real-time.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6 flex items-start space-x-4">
          <div className="p-3 bg-indigo-500/20 rounded-xl">
            <Activity className="w-6 h-6 text-indigo-400" />
          </div>
          <div>
            <p className="text-sm text-slate-400 font-medium uppercase tracking-wider">Active Workflows</p>
            <p className="text-3xl font-bold text-white mt-1">{workflows.length}</p>
          </div>
        </div>
        
        <div className="glass-card p-6 flex items-start space-x-4">
          <div className="p-3 bg-emerald-500/20 rounded-xl">
            <CheckCircle2 className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <p className="text-sm text-slate-400 font-medium uppercase tracking-wider">Total Executions</p>
            <p className="text-3xl font-bold text-white mt-1">{executions.length}</p>
          </div>
        </div>

        <div className="glass-card p-6 flex items-start space-x-4">
          <div className="p-3 bg-amber-500/20 rounded-xl">
            <Zap className="w-6 h-6 text-amber-400" />
          </div>
          <div>
            <p className="text-sm text-slate-400 font-medium uppercase tracking-wider">System Status</p>
            <p className="text-3xl font-bold text-white mt-1 flex items-center">
              <span className="w-3 h-3 rounded-full bg-emerald-500 mr-2 animate-pulse"></span>
              Healthy
            </p>
          </div>
        </div>
      </div>

      <div className="glass-card overflow-hidden">
        <div className="border-b border-slate-800 p-6 flex justify-between items-center">
          <h2 className="text-xl font-bold flex items-center">
            <Clock className="w-5 h-5 mr-2 text-indigo-400" />
            Recent Executions
          </h2>
          <button 
            onClick={handleClear}
            className="text-xs font-bold uppercase tracking-wider text-slate-500 hover:text-rose-400 transition-colors flex items-center"
          >
            <Trash2 className="w-4 h-4 mr-1" />
            Clear History
          </button>
        </div>
        <div className="p-0">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-900/50 text-slate-400 text-sm uppercase tracking-wider">
                <th className="p-4 font-medium">ID</th>
                <th className="p-4 font-medium">Workflow</th>
                <th className="p-4 font-medium text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {executions.length === 0 ? (
                <tr>
                  <td colSpan={3} className="p-8 text-center text-slate-500 italic">No execution records found. Start a workflow from the Builder to see it here.</td>
                </tr>
              ) : (
                executions.map((exe: any) => (
                  <tr 
                    key={exe.id} 
                    onClick={() => openDetails(exe.id)}
                    className="hover:bg-indigo-500/5 transition-colors cursor-pointer group"
                  >
                    <td className="p-4 text-slate-400 font-mono text-sm">#{exe.id}</td>
                    <td className="p-4 font-semibold text-slate-200">
                      Workflow {exe.workflow_id}
                      <span className="ml-2 opacity-0 group-hover:opacity-100 transition-opacity text-indigo-400 inline-block align-middle">
                        <ChevronRight className="w-4 h-4" />
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <span className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest border ${
                        exe.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 
                        exe.status === 'failed' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' : 
                        'bg-amber-500/10 text-amber-400 border-amber-500/20'
                      }`}>
                        {exe.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Execution Details Modal */}
      {selectedExecution && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in">
          <div className="glass-card w-full max-w-2xl overflow-hidden shadow-2xl border-indigo-500/30">
            <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-indigo-500/5">
              <h3 className="text-xl font-bold flex items-center">
                <Activity className="w-5 h-5 mr-2 text-indigo-400" />
                Execution Details #{selectedExecution.id}
              </h3>
              <button onClick={() => setSelectedExecution(null)} className="p-2 hover:bg-slate-800 rounded-full transition-colors text-slate-400 hover:text-white">
                <X className="w-6 h-6" />
              </button>
            </div>
            
            <div className="p-8 space-y-6 max-h-[70vh] overflow-y-auto">
              <div className="grid grid-cols-3 gap-6">
                <div>
                  <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Status</p>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-widest border ${
                    selectedExecution.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 
                    selectedExecution.status === 'failed' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' : 
                    'bg-amber-500/10 text-amber-400 border-amber-500/20'
                  }`}>
                    {selectedExecution.status}
                  </span>
                </div>
                <div>
                  <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Workflow ID</p>
                  <p className="text-lg font-mono text-white">{selectedExecution.workflow_id}</p>
                </div>
                <div>
                  <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Tokens Used</p>
                  <p className="text-lg font-mono text-white">
                    {selectedExecution.result?.tokens ? selectedExecution.result.tokens.toLocaleString() : "N/A"}
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Agent Results / Output</p>
                <div className="bg-slate-950/80 rounded-xl p-4 border border-slate-800 font-mono text-sm text-indigo-100 overflow-x-auto whitespace-pre-wrap min-h-[100px]">
                  {selectedExecution.result ? (
                    typeof selectedExecution.result === 'string' 
                      ? selectedExecution.result 
                      : (selectedExecution.result.output || JSON.stringify(selectedExecution.result, null, 2))
                  ) : (
                    <span className="text-slate-600 italic">No output data available yet.</span>
                  )}
                </div>
              </div>
            </div>

            <div className="p-6 bg-slate-900/50 border-t border-slate-800 text-right">
              <button 
                onClick={() => setSelectedExecution(null)}
                className="bg-slate-800 hover:bg-slate-700 text-white px-6 py-2 rounded-lg font-bold transition-all"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {loadingDetails && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/20 backdrop-blur-[2px]">
          <Loader2 className="w-12 h-12 text-indigo-500 animate-spin" />
        </div>
      )}
    </div>
  );
}

