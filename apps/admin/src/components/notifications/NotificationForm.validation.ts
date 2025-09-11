import { z } from 'zod';

import type { NotificationErrors, NotificationFormValues } from './NotificationFormCore';

const schema = z.object({
  title: z.string().min(1, 'Title required'),
  message: z.string().min(1, 'Message required'),
});

export function validateNotification(values: Pick<NotificationFormValues, 'title' | 'message'>): {
  valid: boolean;
  errors: NotificationErrors;
} {
  const res = schema.safeParse({ title: values.title, message: values.message });
  return {
    valid: res.success,
    errors: {
      title: res.success ? null : (res.error.formErrors.fieldErrors.title?.[0] ?? null),
      message: res.success ? null : (res.error.formErrors.fieldErrors.message?.[0] ?? null),
    },
  };
}
