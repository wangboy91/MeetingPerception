import { AssistantRoleOption } from "@meeting-copilot/shared";

export const ASSISTANT_ROLE_OPTIONS: AssistantRoleOption[] = [
  {
    id: "tech-review",
    label: "技术评审助手",
    description: "聚焦接口、数据一致性、异常路径和回滚风险",
  },
  {
    id: "product-review",
    label: "需求评审助手",
    description: "聚焦范围边界、优先级、验收标准和需求变更",
  },
  {
    id: "sales",
    label: "销售沟通助手",
    description: "聚焦客户痛点、预算、决策链和下一步推进",
  },
  {
    id: "management",
    label: "管理会议助手",
    description: "聚焦决策、责任人、截止时间和执行风险",
  },
];
