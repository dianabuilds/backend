import { useId } from 'react';

export type NotificationFormValues = {
  title: string;
  message: string;
  type: 'system' | 'info' | 'warning' | 'quest';
};

export type NotificationErrors = {
  title: string | null;
  message: string | null;
};

// validation moved to NotificationForm.validation.ts to satisfy react-refresh rule

type FieldsProps = {
  values: NotificationFormValues;
  onChange: (patch: Partial<NotificationFormValues>) => void;
  errors?: NotificationErrors;
  disabled?: boolean;
  multilineMessage?: boolean;
};

export function NotificationFormFields({
  values,
  onChange,
  errors,
  disabled,
  multilineMessage,
}: FieldsProps) {
  const baseId = useId();
  const titleId = `${baseId}-title`;
  const messageId = `${baseId}-message`;
  const typeId = `${baseId}-type`;
  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-col">
        <label htmlFor={titleId} className="text-sm text-gray-600">
          Title
        </label>
        <input
          id={titleId}
          className="border rounded px-2 py-1"
          value={values.title}
          onChange={(e) => onChange({ title: e.target.value })}
          disabled={disabled}
        />
        {errors?.title && <span className="text-xs text-red-600">{errors.title}</span>}
      </div>
      <div className="flex flex-col">
        <label htmlFor={typeId} className="text-sm text-gray-600">
          Type
        </label>
        <select
          id={typeId}
          className="border rounded px-2 py-1"
          value={values.type}
          onChange={(e) => onChange({ type: e.target.value as NotificationFormValues['type'] })}
          disabled={disabled}
        >
          <option value="system">system</option>
          <option value="info">info</option>
          <option value="warning">warning</option>
          <option value="quest">quest</option>
        </select>
      </div>
      <div className="flex flex-col">
        <label htmlFor={messageId} className="text-sm text-gray-600">
          Message
        </label>
        {multilineMessage ? (
          <textarea
            id={messageId}
            className="border rounded px-2 py-1"
            rows={3}
            value={values.message}
            onChange={(e) => onChange({ message: e.target.value })}
            disabled={disabled}
          />
        ) : (
          <input
            id={messageId}
            className="border rounded px-2 py-1"
            value={values.message}
            onChange={(e) => onChange({ message: e.target.value })}
            disabled={disabled}
          />
        )}
        {errors?.message && <span className="text-xs text-red-600">{errors.message}</span>}
      </div>
    </div>
  );
}
