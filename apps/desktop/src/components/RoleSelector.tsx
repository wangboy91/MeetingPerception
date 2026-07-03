import { AssistantRole } from "@meeting-copilot/shared";

import { ASSISTANT_ROLE_OPTIONS } from "../services/assistantRoles";

interface RoleSelectorProps {
  value: AssistantRole;
  onChange: (role: AssistantRole) => void;
}

export function RoleSelector({ value, onChange }: RoleSelectorProps) {
  const selectedRole = ASSISTANT_ROLE_OPTIONS.find((role) => role.id === value);

  return (
    <label className="role-selector">
      <span>助手角色</span>
      <select value={value} onChange={(event) => onChange(event.target.value as AssistantRole)}>
        {ASSISTANT_ROLE_OPTIONS.map((role) => (
          <option key={role.id} value={role.id}>
            {role.label}
          </option>
        ))}
      </select>
      <small>{selectedRole?.description}</small>
    </label>
  );
}
