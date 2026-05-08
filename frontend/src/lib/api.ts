const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function fetchAgents() {
  const res = await fetch(`${API_URL}/agents`);
  if (!res.ok) throw new Error("Failed to fetch agents");
  return res.json();
}

export async function createAgent(data: any) {
  const res = await fetch(`${API_URL}/agents`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create agent");
  return res.json();
}

export async function updateAgent(id: number, data: any) {
  const res = await fetch(`${API_URL}/agents/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update agent");
  return res.json();
}

export async function deleteAgent(id: number) {
  const res = await fetch(`${API_URL}/agents/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete agent");
  return res.json();
}

export async function fetchWorkflows() {
  const res = await fetch(`${API_URL}/workflows`);
  if (!res.ok) throw new Error("Failed to fetch workflows");
  return res.json();
}

export async function createWorkflow(data: any) {
  const res = await fetch(`${API_URL}/workflows`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create workflow");
  return res.json();
}

export async function deleteWorkflow(id: number) {
  const res = await fetch(`${API_URL}/workflows/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete workflow");
  return res.json();
}

export async function executeWorkflow(id: number, message: string) {
  const res = await fetch(`${API_URL}/workflows/${id}/execute?input_message=${encodeURIComponent(message)}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to execute workflow");
  return res.json();
}

export async function fetchExecution(id: number) {
  const res = await fetch(`${API_URL}/executions/${id}`);
  if (!res.ok) throw new Error("Failed to fetch execution status");
  return res.json();
}

export async function fetchRecentExecutions() {
  const res = await fetch(`${API_URL}/executions`);
  if (!res.ok) throw new Error("Failed to fetch executions");
  return res.json();
}

export async function clearExecutions() {
  const res = await fetch(`${API_URL}/executions`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to clear executions");
  return res.json();
}

