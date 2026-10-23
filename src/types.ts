export type Profile = {
  id: string;
  email: string;
  fullName: string;
  role: string;
  permissions: string[];
};

export type FieldType = "text" | "password" | "textarea" | "number" | "date" | "boolean" | "select";

export type FieldDefinition = {
  key: string;
  label: string;
  type?: FieldType;
  required?: boolean;
  options?: string[];
};

export type ColumnDefinition = {
  key: string;
  label: string;
  format?: "money" | "date" | "boolean";
};

export type ModuleDefinition = {
  id: string;
  title: string;
  table: string;
  permission: string;
  select?: string;
  columns: ColumnDefinition[];
  fields: FieldDefinition[];
  createFields?: FieldDefinition[];
  actions?: Array<"movement" | "variant" | "whatsapp" | "convert" | "status">;
  allowCreate?: boolean;
};

export type UpdateStatus = {
  status: string;
  detail?: { version?: string; percent?: number } | string;
};
