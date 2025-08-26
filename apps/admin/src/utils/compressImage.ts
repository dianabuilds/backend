export async function compressImage(
  file: File,
  maxSize = 8 * 1024 * 1024,
  type: string = 'image/jpeg',
): Promise<File> {
  const bitmap = await createImageBitmap(file);
  const canvas = document.createElement('canvas');
  canvas.width = bitmap.width;
  canvas.height = bitmap.height;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('Canvas unsupported');
  ctx.drawImage(bitmap, 0, 0);
  let quality = 0.9;
  let blob: Blob | null = await new Promise((resolve) => canvas.toBlob(resolve, type, quality));
  while (blob && blob.size > maxSize && quality > 0.4) {
    quality -= 0.1;
    blob = await new Promise((resolve) => canvas.toBlob(resolve, type, quality));
  }
  if (!blob) throw new Error('Compression failed');
  if (blob.size > maxSize) throw new Error('Image too large');
  return new File([blob], file.name.replace(/\.[^.]+$/, '.jpg'), { type });
}
