import { http } from "./request";

/** 预设对话项 */
export interface PresetDialogue {
  role: "user" | "assistant";
  content: string;
}

/** 提示词配置基础类型 */
export interface PromptConfig {
  id: number;
  prompt_id: string;
  prompt_name: string;
  description?: string;
  system_prompt: string;
  variables?: string[];
  temperature_override?: number;
  is_active: boolean;
  selected_tools?: string[];
  use_all_tools: boolean;
  preset_dialogues?: PresetDialogue[];
  created_at?: string;
  updated_at?: string;
}

/** 提示词配置列表项 */
export interface PromptConfigListItem {
  prompt_id: string; // 用于删除等操作
  prompt_name: string;
  description?: string;
  system_prompt: string; // 系统提示词
  is_active: boolean;
  created_at?: string; // 创建时间
}

/** 创建提示词配置请求 */
export interface CreatePromptConfigRequest {
  prompt_name: string;
  description?: string;
  system_prompt: string;
  variables?: string[];
  temperature_override?: number;
  is_active?: boolean;
  selected_tools?: string[];
  use_all_tools?: boolean;
  preset_dialogues?: PresetDialogue[];
}

/** 更新提示词配置请求 */
export interface UpdatePromptConfigRequest {
  prompt_name?: string;
  description?: string;
  system_prompt?: string;
  variables?: string[];
  temperature_override?: number;
  is_active?: boolean;
  selected_tools?: string[];
  use_all_tools?: boolean;
  preset_dialogues?: PresetDialogue[];
}

/** API 响应包装 */
export interface ApiResponse<T> {
  code?: number;
  message?: string;
  data: T;
}

/**
 * 获取提示词配置列表
 */
export const getPromptConfigList = async (): Promise<
  ApiResponse<PromptConfigListItem[]>
> => {
  const response =
    await http.get<ApiResponse<PromptConfigListItem[]>>("/prompts");
  return response;
};

/**
 * 获取提示词配置详情
 */
export const getPromptConfigDetail = async (
  promptId: string,
): Promise<ApiResponse<PromptConfig>> => {
  const response = await http.get<ApiResponse<PromptConfig>>(
    `/prompts/${promptId}`,
  );
  return response;
};

/**
 * 创建提示词配置
 */
export const createPromptConfig = async (
  data: CreatePromptConfigRequest,
): Promise<ApiResponse<PromptConfig>> => {
  const response = await http.post<ApiResponse<PromptConfig>>("/prompts", data);
  return response;
};

/**
 * 更新提示词配置
 */
export const updatePromptConfig = async (
  promptId: string,
  data: UpdatePromptConfigRequest,
): Promise<ApiResponse<PromptConfig>> => {
  const response = await http.put<ApiResponse<PromptConfig>>(
    `/prompts/${promptId}`,
    data,
  );
  return response;
};

/**
 * 删除提示词配置
 */
export const deletePromptConfig = async (
  promptId: string,
): Promise<ApiResponse<void>> => {
  const response = await http.delete<ApiResponse<void>>(`/prompts/${promptId}`);
  return response;
};
