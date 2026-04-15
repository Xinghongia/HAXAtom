import { http } from "./request";

export interface Plugin {
  id: string;
  name: string;
  description: string;
  version?: string;
  author?: string;
  source: "builtin" | "skill" | "mcp" | "community";
  icon?: string;
  category?: string;
  tags?: string[];
  enabled: boolean;
  config_schema?: Record<string, unknown>;
  default_config?: Record<string, unknown>;
}

export const pluginApi = {
  list: () => http.get<{ data: Plugin[] }>("/plugins"),

  get: (id: string) => http.get<{ data: Plugin }>(`/plugins/${id}`),

  enable: (id: string) => http.post<{ data: Plugin }>(`/plugins/${id}/enable`),

  disable: (id: string) =>
    http.post<{ data: Plugin }>(`/plugins/${id}/disable`),
};
