import { apiRequestRaw, type ApiRequestOptions } from './base';

export type UploadPayload =
  | FormData
  | File
  | Blob
  | {
      file?: File | Blob;
      files?: Array<File | Blob>;
      fields?: Record<string, string | Blob>;
      fieldName?: string;
    };

function toFormData(payload: UploadPayload): FormData {
  if (payload instanceof FormData) return payload;
  const form = new FormData();
  if (payload instanceof File || payload instanceof Blob) {
    form.append('file', payload);
    return form;
  }
  const cast = payload as Record<string, unknown>;
  const name = typeof cast.fieldName === 'string' && cast.fieldName.trim().length ? cast.fieldName : 'file';
  if (cast.file instanceof File || cast.file instanceof Blob) {
    form.append(name, cast.file);
  }
  if (Array.isArray(cast.files)) {
    for (const file of cast.files) {
      if (file instanceof File || file instanceof Blob) {
        form.append(name, file);
      }
    }
  }
  if (cast.fields && typeof cast.fields === 'object') {
    for (const [key, value] of Object.entries(cast.fields)) {
      if (value instanceof Blob) form.append(key, value);
      else if (typeof value === 'string') form.append(key, value);
    }
  }
  return form;
}

export type UploadOptions = {
  method?: string;
  omitCredentials?: boolean;
  headers?: Record<string, string>;
};

export function apiUploadMedia(path: string, payload: UploadPayload, opts?: UploadOptions): Promise<any>;
export function apiUploadMedia(payload: UploadPayload, opts?: UploadOptions): Promise<any>;
export async function apiUploadMedia(
  pathOrPayload: string | UploadPayload,
  payloadOrOpts?: UploadPayload | UploadOptions,
  maybeOpts: UploadOptions = {}
): Promise<any> {
  const path = typeof pathOrPayload === 'string' ? pathOrPayload : '/v1/media';
  const payload: UploadPayload = typeof pathOrPayload === 'string'
    ? (payloadOrOpts as UploadPayload)
    : (pathOrPayload as UploadPayload);
  if (payload == null) throw new Error('payload_required');
  const opts = typeof pathOrPayload === 'string'
    ? maybeOpts
    : (payloadOrOpts as UploadOptions | undefined) || {};

  const form = toFormData(payload);
  const requestOptions: ApiRequestOptions = {
    method: opts.method || 'POST',
    body: form,
    headers: opts.headers,
    omitCredentials: opts.omitCredentials,
  };

  const response = await apiRequestRaw(path, requestOptions);
  try {
    return await response.json();
  } catch {
    return true;
  }
}