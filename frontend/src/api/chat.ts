/**
 * 对话 API 模块
 *
 * 提供对话相关的接口调用
 */

import { http } from "./request";

// 对话请求参数
export interface ChatRequest {
  preset_id: string;
  message: string;
  session_id?: string;
  stream?: boolean;
  enable_tools?: boolean;
  enable_rag?: boolean;
  enable_memory?: boolean;
  channel_type?: string;
  channel_id?: string;
}

// 对话响应
export interface ChatResponse {
  content: string;
  session_id: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

// 统一响应格式
export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
  timestamp: number;
}

// 会话详情
export interface Conversation {
  id: number;
  session_id: string;
  channel_type: string;
  channel_id?: string;
  preset_id: string;
  title: string;
  message_count: number;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

// 消息
export interface Message {
  role: "system" | "user" | "assistant" | "tool";
  content: string;
  name?: string;
  tool_calls?: any[];
  tool_call_id?: string;
}

// 预设方案
export interface Preset {
  preset_id: string;
  preset_name: string;
  description?: string;
  selected_model: string;
  selected_prompt?: string;
  selected_memory?: string;
  selected_plugins?: string[];
  selected_knowledge_bases?: string[];
  is_default?: boolean;
  is_active?: boolean;
}

/**
 * 发送对话请求（非流式）
 */
export const sendChatMessage = async (
  params: ChatRequest,
): Promise<ApiResponse<ChatResponse>> => {
  return http.post<ApiResponse<ChatResponse>>("/chat/completions", params);
};

/**
 * 发送对话请求（流式）
 *
 * 使用 SSE (Server-Sent Events) 接收流式响应
 */
export const sendChatMessageStream = async (
  params: ChatRequest,
  onChunk: (chunk: string) => void,
  onComplete: (fullResponse: string, sessionId: string) => void | Promise<void>,
  onError: (error: Error) => void,
): Promise<void> => {
  const response = await fetch("/api/v1/chat/completions/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${localStorage.getItem("token") || ""}`,
    },
    body: JSON.stringify({
      ...params,
      stream: true,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    onError(new Error(errorData.detail || "请求失败"));
    return;
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  let fullResponse = "";
  let sessionId = "";
  let buffer = "";

  if (!reader) {
    onError(new Error("无法读取响应流"));
    return;
  }

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || ""; // 保留最后一行可能不完整的数据

      for (const line of lines) {
        const trimmedLine = line.trim();

        // 处理 SSE 格式：data: {...}
        if (trimmedLine.startsWith("data: ")) {
          const data = trimmedLine.slice(6).trim();
          if (data === "[DONE]") continue;

          try {
            const parsed = JSON.parse(data);
            if (parsed.content) {
              fullResponse += parsed.content;
              onChunk(parsed.content);
            }
            if (parsed.session_id) {
              sessionId = parsed.session_id;
            }
            // 检查是否结束
            if (parsed.is_end === true) {
              break;
            }
          } catch (e) {
            console.warn("解析 SSE 数据失败:", e, data);
          }
        }
      }
    }

    await onComplete(fullResponse, sessionId);
  } catch (error) {
    onError(error instanceof Error ? error : new Error("流式读取失败"));
  } finally {
    reader.releaseLock();
  }
};

/**
 * 获取会话详情
 */
export const getConversation = async (
  sessionId: string,
): Promise<ApiResponse<Conversation>> => {
  return http.get<ApiResponse<Conversation>>(
    `/chat/conversations/${sessionId}`,
  );
};

/**
 * 获取会话列表
 */
export const listConversations = async (params?: {
  preset_id?: string;
  channel_type?: string;
  skip?: number;
  limit?: number;
}): Promise<ApiResponse<Conversation[]>> => {
  const queryParams = new URLSearchParams();
  if (params?.preset_id) queryParams.append("preset_id", params.preset_id);
  if (params?.channel_type)
    queryParams.append("channel_type", params.channel_type);
  if (params?.skip !== undefined)
    queryParams.append("skip", String(params.skip));
  if (params?.limit !== undefined)
    queryParams.append("limit", String(params.limit));

  const query = queryParams.toString();
  return http.get<ApiResponse<Conversation[]>>(
    `/chat/conversations${query ? `?${query}` : ""}`,
  );
};

/**
 * 清空会话消息
 */
export const clearConversation = async (
  sessionId: string,
): Promise<ApiResponse<Conversation>> => {
  return http.post<ApiResponse<Conversation>>(
    `/chat/conversations/${sessionId}/clear`,
  );
};

/**
 * 删除会话
 */
export const deleteConversation = async (
  sessionId: string,
): Promise<ApiResponse<{ success: boolean }>> => {
  return http.delete<ApiResponse<{ success: boolean }>>(
    `/chat/conversations/${sessionId}`,
  );
};

/**
 * 获取预设方案列表
 */
export const listPresets = async (): Promise<ApiResponse<Preset[]>> => {
  return http.get<ApiResponse<Preset[]>>("/presets");
};

/**
 * 获取默认预设
 */
export const getDefaultPreset = async (): Promise<ApiResponse<Preset>> => {
  return http.get<ApiResponse<Preset>>("/presets/default");
};
