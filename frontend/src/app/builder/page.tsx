"use client";

import { useState, useCallback, useEffect, useRef } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Handle,
  Position,
  useReactFlow,
  ReactFlowProvider
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { fetchAgents, fetchWorkflows, createWorkflow, executeWorkflow, fetchExecution, deleteWorkflow } from '@/lib/api';
import { Save, Play, GitFork, Cpu, Zap, X, Loader2, RotateCcw, CheckCircle, AlertCircle, Trash2, ChevronDown, ChevronUp } from 'lucide-react';

// Custom Node Components
const AgentNode = ({ id, data = {} }: any) => {
  const { setNodes, setEdges } = useReactFlow();

  const onDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    setNodes((nds) => nds.filter((node) => node.id !== id));
    setEdges((eds) => eds.filter((edge) => edge.source !== id && edge.target !== id));
  };

  return (
    <div className="react-flow__node-agent flex items-center space-x-3 relative group">
      <button 
        onClick={onDelete} 
        className="absolute -top-3 -right-3 bg-red-500 hover:bg-red-600 rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity z-10 shadow-lg cursor-pointer"
        title="Remove Agent"
      >
        <X className="w-3 h-3 text-white" />
      </button>
      <Handle type="target" position={Position.Top} />
      <div className="p-2 bg-indigo-500/20 rounded-lg">
        <Cpu className="w-5 h-5 text-indigo-400" />
      </div>
      <div>
        <div className="text-xs text-slate-500 font-bold uppercase tracking-tighter">Agent</div>
        <div className="text-sm font-semibold text-white">{data.label || 'Agent'}</div>
      </div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

const TriggerNode = ({ data = {} }: any) => (
  <div className="react-flow__node-input flex items-center space-x-3">
    <div className="p-2 bg-emerald-500/20 rounded-lg">
      <Zap className="w-5 h-5 text-emerald-400" />
    </div>
    <div>
      <div className="text-xs text-slate-500 font-bold uppercase tracking-tighter">Trigger</div>
      <div className="text-sm font-semibold text-white">{data.label || 'Start Trigger'}</div>
    </div>
    <Handle type="source" position={Position.Bottom} />
  </div>
);

const ConditionNode = ({ id, data = {} }: any) => {
  const { setNodes, setEdges } = useReactFlow();

  const onDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    setNodes((nds) => nds.filter((node) => node.id !== id));
    setEdges((eds) => eds.filter((edge) => edge.source !== id && edge.target !== id));
  };

  const updateCondition = (val: string) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === id) {
          return { ...node, data: { ...node.data, condition: val } };
        }
        return node;
      })
    );
  };

  return (
    <div className="react-flow__node-condition p-4 glass-card border-indigo-500/30 min-w-[200px] group">
      <button 
        onClick={onDelete} 
        className="absolute -top-3 -right-3 bg-red-500 hover:bg-red-600 rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity z-10 shadow-lg cursor-pointer"
      >
        <X className="w-3 h-3 text-white" />
      </button>
      <Handle type="target" position={Position.Top} />
      
      <div className="flex items-center space-x-3 mb-3">
        <div className="p-2 bg-indigo-500/20 rounded-lg">
          <GitFork className="w-5 h-5 text-indigo-400" />
        </div>
        <div className="text-xs text-slate-500 font-bold uppercase tracking-tighter">Condition</div>
      </div>
      
      <input 
        type="text" 
        value={data.condition || ''} 
        onChange={(e) => updateCondition(e.target.value)}
        placeholder="e.g. contains 'error'"
        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
      />

      <div className="flex justify-between mt-4">
        <div className="relative">
          <Handle type="source" position={Position.Bottom} id="true" style={{ left: '25%', background: '#10b981' }} />
          <span className="text-[10px] text-emerald-400 font-bold absolute -bottom-4 left-0">TRUE</span>
        </div>
        <div className="relative">
          <Handle type="source" position={Position.Bottom} id="false" style={{ left: '75%', background: '#f43f5e' }} />
          <span className="text-[10px] text-rose-400 font-bold absolute -bottom-4 right-0">FALSE</span>
        </div>
      </div>
    </div>
  );
};

const nodeTypes = {
  agent: AgentNode,
  trigger: TriggerNode,
  condition: ConditionNode,
};

const initialNodes = [
  { id: 'trigger', type: 'trigger', data: { label: 'External Input' }, position: { x: 250, y: 5 } },
];

const LogItem = ({ log }: { log: any }) => {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="border-b border-slate-800/50 last:border-0 py-2">
      <button 
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between text-[11px] text-slate-300 hover:text-emerald-400 transition-colors"
      >
        <div className="flex items-center">
          <span className="font-mono text-slate-500 mr-2">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
          <span className="truncate max-w-[200px]">{log.message}</span>
        </div>
        {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      </button>
      {expanded && (
        <div className="mt-2 p-2 bg-black/40 rounded text-[10px] font-mono text-emerald-100 whitespace-pre-wrap break-words border border-slate-800">
          {log.message}
        </div>
      )}
    </div>
  );
};

function Builder() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [agents, setAgents] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<any>(null);
  const [execMessage, setExecMessage] = useState("Hello");
  
  // Agent details modal state
  const [inspectingAgent, setInspectingAgent] = useState<any>(null);
  
  // Execution state
  const [executionStatus, setExecutionStatus] = useState<null | 'running' | 'completed' | 'failed'>(null);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  // Load persistence
  useEffect(() => {
    const savedNodes = localStorage.getItem('agent_orch_nodes');
    const savedEdges = localStorage.getItem('agent_orch_edges');
    if (savedNodes) setNodes(JSON.parse(savedNodes));
    if (savedEdges) setEdges(JSON.parse(savedEdges));

    fetchAgents().then(setAgents).catch(console.error);
    fetchWorkflows().then(setWorkflows).catch(console.error);

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  // Save persistence
  useEffect(() => {
    localStorage.setItem('agent_orch_nodes', JSON.stringify(nodes));
    localStorage.setItem('agent_orch_edges', JSON.stringify(edges));
  }, [nodes, edges]);

  const onConnect = useCallback((params: Connection | Edge) => setEdges((eds) => addEdge({ ...params, animated: true }, eds)), [setEdges]);

  const addAgentNode = (agent: any) => {
    const newNode = {
      id: `agent_${new Date().getTime()}`,
      type: 'agent',
      position: { x: Math.random() * 300 + 100, y: Math.random() * 300 + 100 },
      data: { label: agent.name, agent_id: agent.id },
    };
    setNodes((nds) => nds.concat(newNode));
  };

  const handleClearCanvas = () => {
    if (confirm("Clear the entire canvas?")) {
      setNodes(initialNodes);
      setEdges([]);
      localStorage.removeItem('agent_orch_nodes');
      localStorage.removeItem('agent_orch_edges');
    }
  };

  const handleSave = async () => {
    const name = prompt("Enter workflow name:");
    if (!name) return;
    
    const backendNodes = nodes.map(n => ({
      id: n.id,
      type: n.type,
      position: n.position,
      data: n.data
    }));

    await createWorkflow({
      name,
      description: "Custom built workflow",
      nodes: backendNodes,
      edges
    });
    alert("Workflow saved to database!");
    fetchWorkflows().then(setWorkflows).catch(console.error);
  };

  const pollExecution = async (id: number) => {
    try {
      const data = await fetchExecution(id);
      setExecutionStatus(data.status);
      setExecutionResult(data); // Store the whole object (id, status, result, logs)
      
      if (data.status === 'completed' || data.status === 'failed') {
        if (pollingRef.current) clearInterval(pollingRef.current);
      }
    } catch (e) {
      console.error("Polling error:", e);
    }
  };



  const handleExecute = async () => {
    if (!selectedWorkflow) {
      alert("Please select a saved workflow to execute (or save this one first).");
      return;
    }
    
    setExecutionStatus('running');
    setExecutionResult(null);
    
    try {
      const res = await executeWorkflow(selectedWorkflow.id, execMessage);
      pollingRef.current = setInterval(() => pollExecution(res.execution_id), 2000);
    } catch (e) {
      setExecutionStatus('failed');
      setExecutionResult({ error: "Failed to start execution" });
    }
  };

  const loadWorkflow = (wf: any) => {
    setSelectedWorkflow(wf);
    const reactFlowNodes = wf.nodes.map((n: any) => ({
      id: n.id,
      type: n.type,
      position: n.position,
      data: n.data
    }));
    setNodes(reactFlowNodes);
    setEdges(wf.edges);
  };

  const onNodeDoubleClick = useCallback((event: React.MouseEvent, node: any) => {
    if (node.type === 'agent') {
      const agentId = node.data.agent_id;
      const agent = agents.find((a: any) => a.id === agentId);
      if (agent) {
        setInspectingAgent(agent);
      }
    }
  }, [agents]);

  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col space-y-6 animate-in fade-in duration-500">
      <header className="flex justify-between items-end">
        <div>
          <h1 className="text-4xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-cyan-400 mb-2 flex items-center">
            <GitFork className="w-8 h-8 mr-3 text-emerald-400" />
            Workflow Builder
          </h1>
          <p className="text-slate-400 text-lg">Design autonomous pipelines by connecting agents.</p>
        </div>
        <div className="flex space-x-4">
          <button 
            onClick={handleClearCanvas}
            className="flex items-center space-x-2 text-slate-500 hover:text-rose-400 transition-colors px-2"
            title="Reset Canvas"
          >
            <RotateCcw className="w-5 h-5" />
          </button>

          <div className="flex items-center space-x-2">
            <select 
              className="bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 focus:outline-none focus:border-emerald-500 text-sm"
              value={selectedWorkflow?.id || ""}
              onChange={(e) => {
                const wf = workflows.find((w: any) => w.id === parseInt(e.target.value));
                if (wf) loadWorkflow(wf);
                else setSelectedWorkflow(null);
              }}
            >
              <option value="">-- Load Existing --</option>
              {workflows.map((wf: any) => (
                <option key={wf.id} value={wf.id}>{wf.name}</option>
              ))}
            </select>
            {selectedWorkflow && (
              <button 
                onClick={async () => {
                  if (confirm(`Delete workflow "${selectedWorkflow.name}"?`)) {
                    await deleteWorkflow(selectedWorkflow.id);
                    setSelectedWorkflow(null);
                    setNodes(initialNodes);
                    setEdges([]);
                    fetchWorkflows().then(setWorkflows).catch(console.error);
                  }
                }}
                className="p-3 text-slate-500 hover:text-red-400 hover:bg-red-400/10 rounded-xl transition-all"
                title="Delete Workflow"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            )}
          </div>

          <button onClick={handleSave} className="flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-white px-6 py-3 rounded-xl font-medium transition-all">
            <Save className="w-5 h-5" />
            <span>Save</span>
          </button>
          
          <div className="flex bg-emerald-600 rounded-xl overflow-hidden shadow-lg shadow-emerald-500/20">
            <input 
              type="text" 
              value={execMessage}
              onChange={e => setExecMessage(e.target.value)}
              className="bg-slate-900 px-4 focus:outline-none w-48 text-sm"
              placeholder="Input trigger..."
            />
            <button 
              disabled={executionStatus === 'running'}
              onClick={handleExecute} 
              className="flex items-center space-x-2 hover:bg-emerald-500 px-6 py-3 font-medium transition-colors disabled:opacity-50"
            >
              {executionStatus === 'running' ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
              <span>Execute</span>
            </button>
          </div>
        </div>
      </header>

      <div className="flex-1 flex gap-6 min-h-0">
        <div className="w-72 glass-card p-4 flex flex-col">
          <h3 className="font-bold mb-4 uppercase tracking-wider text-[10px] text-slate-500 border-b border-slate-800 pb-2">Available Agents</h3>
          <div className="space-y-3 overflow-y-auto flex-1 pr-1 custom-scrollbar">
            {agents.map((agent: any) => (
              <div 
                key={agent.id} 
                className="p-3 bg-slate-900/50 border border-slate-700/50 rounded-xl cursor-pointer hover:border-emerald-500/50 hover:bg-emerald-500/5 transition-all group"
                onClick={() => addAgentNode(agent)}
              >
                <p className="font-bold text-sm text-slate-200 group-hover:text-emerald-400 transition-colors">{agent.name}</p>
                <p className="text-[10px] text-slate-500 mt-1 uppercase tracking-widest">{agent.role}</p>
              </div>
            ))}
          </div>
          <div className="mt-4 p-3 bg-slate-950/50 rounded-xl border border-slate-800">
             <p className="text-[10px] text-slate-500 leading-relaxed">
              Drag from handles to connect agents. Data flows from top to bottom.
             </p>
          </div>

          <h3 className="font-bold mt-6 mb-4 uppercase tracking-wider text-[10px] text-slate-500 border-b border-slate-800 pb-2">Logic</h3>
          <button 
            onClick={() => {
              const newNode = {
                id: `condition_${new Date().getTime()}`,
                type: 'condition',
                position: { x: 400, y: 400 },
                data: { condition: "" },
              };
              setNodes((nds) => nds.concat(newNode));
            }}
            className="w-full p-3 bg-slate-900/50 border border-indigo-500/30 rounded-xl cursor-pointer hover:bg-indigo-500/10 transition-all flex items-center space-x-3 group"
          >
            <GitFork className="w-4 h-4 text-indigo-400" />
            <span className="text-sm font-bold text-slate-200 group-hover:text-indigo-400 transition-colors">Condition Node</span>
          </button>
        </div>

        <div className="flex-1 glass-card overflow-hidden relative">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            onNodeDoubleClick={onNodeDoubleClick}
            className="bg-slate-950/50"
            colorMode="dark"
          >
            <Controls className="bg-slate-900 border-slate-700 fill-slate-300" />
            <MiniMap className="bg-slate-900 border border-slate-800" maskColor="rgba(15, 23, 42, 0.7)" />
            <Background color="#1e293b" gap={16} />
          </ReactFlow>

          {/* Execution Progress Overlay */}
          {executionStatus && (
            <div className="absolute bottom-6 right-6 z-10 w-96 animate-in slide-in-from-bottom-4 duration-300">
               <div className="glass-card shadow-2xl border-emerald-500/30 overflow-hidden">
                  <div className="p-4 bg-slate-900/90 border-b border-slate-800 flex justify-between items-center">
                    <h4 className="text-sm font-bold flex items-center uppercase tracking-widest">
                      {executionStatus === 'running' && <Loader2 className="w-4 h-4 mr-2 text-emerald-400 animate-spin" />}
                      {executionStatus === 'completed' && <CheckCircle className="w-4 h-4 mr-2 text-emerald-400" />}
                      {executionStatus === 'failed' && <AlertCircle className="w-4 h-4 mr-2 text-rose-400" />}
                      Execution Console
                    </h4>
                    <button onClick={() => setExecutionStatus(null)} className="text-slate-500 hover:text-white">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="p-5 space-y-3 bg-slate-950/90">
                    <div className="space-y-1">
                      <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Status</p>
                      <p className={`text-xs font-bold uppercase ${executionStatus === 'failed' ? 'text-rose-400' : 'text-emerald-400'}`}>
                        {executionStatus}
                      </p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Intermediate Steps</p>
                      <div className="bg-black/40 rounded-lg p-3 max-h-48 overflow-y-auto border border-slate-800/50 custom-scrollbar">
                        {executionResult?.logs && executionResult.logs.length > 0 ? (
                          executionResult.logs.map((log: any) => (
                            <LogItem key={log.id} log={log} />
                          ))
                        ) : (
                          <span className="text-slate-600 italic text-[10px]">Processing pipeline...</span>
                        )}
                      </div>
                    </div>

                    {(executionStatus === 'completed' || executionStatus === 'failed') && executionResult?.result && (
                      <div className="space-y-1 animate-in slide-in-from-top-2 duration-300">
                        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Final Result</p>
                        <div className="bg-emerald-500/5 rounded-lg p-3 text-xs font-mono text-emerald-100 border border-emerald-500/20 whitespace-pre-wrap">
                          {typeof executionResult.result === 'string' 
                            ? executionResult.result 
                            : (executionResult.result.output || JSON.stringify(executionResult.result, null, 2))}
                        </div>
                      </div>
                    )}
                  </div>
               </div>
            </div>
          )}
        </div>
      </div>

      {/* Agent Inspection Modal */}
      {inspectingAgent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in">
          <div className="glass-card w-full max-w-xl overflow-hidden shadow-2xl border-emerald-500/30">
            <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-emerald-500/5">
              <h3 className="text-xl font-bold flex items-center">
                <Cpu className="w-5 h-5 mr-2 text-emerald-400" />
                Agent Configuration
              </h3>
              <button onClick={() => setInspectingAgent(null)} className="p-2 hover:bg-slate-800 rounded-full transition-colors text-slate-400 hover:text-white">
                <X className="w-6 h-6" />
              </button>
            </div>
            
            <div className="p-8 space-y-6">
              <div>
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">Name</p>
                <p className="text-xl font-bold text-white">{inspectingAgent.name}</p>
                <p className="text-xs text-slate-400 mt-1">{inspectingAgent.role}</p>
              </div>

              <div>
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">Model & Temperature</p>
                <div className="flex space-x-3">
                  <span className="px-3 py-1 bg-slate-900 rounded-lg text-xs font-mono text-emerald-400 border border-slate-800">
                    {inspectingAgent.model_name}
                  </span>
                  <span className="px-3 py-1 bg-slate-900 rounded-lg text-xs font-mono text-slate-400 border border-slate-800">
                    Temp: {inspectingAgent.temperature}
                  </span>
                </div>
              </div>

              <div>
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">System Prompt</p>
                <div className="bg-slate-950/80 rounded-xl p-4 border border-slate-800 text-sm text-slate-300 italic leading-relaxed">
                  "{inspectingAgent.system_prompt}"
                </div>
              </div>

              <div>
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">Available Tools</p>
                <div className="flex flex-wrap gap-2 mt-2">
                  {inspectingAgent.tools && inspectingAgent.tools.length > 0 ? (
                    inspectingAgent.tools.map((tool: string) => (
                      <span key={tool} className="px-2 py-1 bg-emerald-500/10 text-emerald-400 rounded text-[10px] font-bold border border-emerald-500/20">
                        {tool.toUpperCase()}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-600 italic">No tools configured for this agent.</span>
                  )}
                </div>
              </div>
            </div>

            <div className="p-6 bg-slate-900/50 border-t border-slate-800 text-right">
              <button 
                onClick={() => setInspectingAgent(null)}
                className="bg-emerald-600 hover:bg-emerald-500 text-white px-8 py-2 rounded-lg font-bold transition-all shadow-lg shadow-emerald-500/20"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function BuilderPage() {
  return (
    <ReactFlowProvider>
      <Builder />
    </ReactFlowProvider>
  );
}

