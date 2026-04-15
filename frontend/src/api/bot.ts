import { http } from "./request";

export type ChannelType = "onebot11" | "feishu" | "dingtalk" | "telegram" | "qqofficial";

export interface BotResponse {
  bot_id: string;
  bot_name: string;
  channel_type: ChannelType;
  preset_id: string;
  is_active: boolean;
}

export interface BotDetailResponse extends BotResponse {
  channel_config?: {
    listen_host?: string;
    listen_port?: number;
    token?: string;
    message_post_format?: "array" | "string";
    self_message?: boolean;
    is_active?: boolean;
  };
}

export interface BotCreate {
  bot_id: string;
  bot_name: string;
  channel_type: ChannelType;
  preset_id: string;
  is_active?: boolean;
}

export interface BotUpdate {
  bot_name?: string;
  preset_id?: string;
  is_active?: boolean;
}

export const botApi = {
  list: () => http.get<{ data: BotResponse[] }>("/bots"),

  get: (bot_id: string) => http.get<{ data: BotDetailResponse }>(`/bots/${bot_id}`),

  create: (data: BotCreate) => http.post<{ data: BotResponse }>("/bots", data),

  update: (bot_id: string, data: BotUpdate) =>
    http.put<{ data: BotResponse }>(`/bots/${bot_id}`, data),

  delete: (bot_id: string) => http.delete(`/bots/${bot_id}`),
};

export const channelTypeLabels: Record<ChannelType, string> = {
  onebot11: "OneBot v11",
  feishu: "飞书",
  dingtalk: "钉钉",
  telegram: "Telegram",
  qqofficial: "QQ 官方",
};

export const channelTypeColors: Record<ChannelType, string> = {
  onebot11: "#409eff",
  feishu: "#67c23a",
  dingtalk: "#e6a23c",
  telegram: "#909399",
  qqofficial: "#f56c6c",
};