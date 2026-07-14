import api from "@/lib/api";

export const authService = {
  async login(email: string, password: string) {
    const form = new FormData();
    form.append("username", email);
    form.append("password", password);
    const res = await api.post("/auth/login", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data as { access_token: string; token_type: string };
  },

  async register(email: string, password: string, full_name: string) {
    const res = await api.post("/auth/register", { email, password, full_name });
    return res.data;
  },
};

export const gatewayService = {
  async chat(messages: object[], model: string) {
    const res = await api.post("/gateway/chat", { messages, model });
    return res.data;
  },
  async listModels() {
    const res = await api.get("/gateway/models");
    return res.data as Record<string, string[]>;
  },
};

export const ragService = {
  async uploadDocument(projectId: string, file: File) {
    const form = new FormData();
    form.append("project_id", projectId);
    form.append("file", file);
    const res = await api.post("/rag/upload", form);
    return res.data;
  },
  async listDocuments(projectId: string) {
    const res = await api.get("/rag/documents", { params: { project_id: projectId } });
    return res.data;
  },
  async query(projectId: string, question: string, model = "gpt-4o") {
    const res = await api.post("/rag/query", { project_id: projectId, question, model });
    return res.data;
  },
};

export const agentService = {
  async createAgent(data: { project_id: string; name: string; system_prompt: string; model: string }) {
    const res = await api.post("/agents/", data);
    return res.data;
  },
  async listAgents(projectId: string) {
    const res = await api.get("/agents/", { params: { project_id: projectId } });
    return res.data;
  },
  async chat(agentId: string, userId: string, message: string) {
    const res = await api.post(`/agents/${agentId}/chat`, { user_id: userId, message });
    return res.data;
  },
};

export const mcpService = {
  async listTools() {
    const res = await api.get("/mcp/tools");
    return res.data;
  },
  async callTool(name: string, args: object) {
    const res = await api.post("/mcp/tools/call", { name, arguments: args });
    return res.data;
  },
};

export const workflowService = {
  async listWorkflows(projectId: string) {
    const res = await api.get("/workflows/", { params: { project_id: projectId } });
    return res.data;
  },
  async createWorkflow(data: { project_id: string; name: string; description?: string; definition: object }) {
    const res = await api.post("/workflows/", data);
    return res.data;
  },
  async executeWorkflow(workflowId: string, inputData: object) {
    const res = await api.post(`/workflows/${workflowId}/run`, { input_data: inputData });
    return res.data;
  },
  async getWorkflowRuns(workflowId: string) {
    const res = await api.get(`/workflows/${workflowId}/runs`);
    return res.data;
  },
};
