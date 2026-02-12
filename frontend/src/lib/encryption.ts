export async function encryptFile(file: File): Promise<{ encrypted: ArrayBuffer; key: string }> {
  const key = crypto.getRandomValues(new Uint8Array(32));
  const iv = crypto.getRandomValues(new Uint8Array(12));

  const cryptoKey = await crypto.subtle.importKey(
    "raw", key, "AES-GCM", false, ["encrypt"]
  );

  const fileBuffer = await file.arrayBuffer();
  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv }, cryptoKey, fileBuffer
  );

  // Format: nonce(12) + ciphertext + tag (WebCrypto appends tag automatically)
  const result = new Uint8Array(iv.length + ciphertext.byteLength);
  result.set(iv, 0);
  result.set(new Uint8Array(ciphertext), iv.length);

  const keyB64 = btoa(String.fromCharCode(...key));

  return { encrypted: result.buffer, key: keyB64 };
}
