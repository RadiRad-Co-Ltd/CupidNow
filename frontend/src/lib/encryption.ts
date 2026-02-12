// Client-side AES encryption was removed intentionally.
//
// Reason: sending the AES key alongside the encrypted file in the same
// HTTPS request provides no additional security beyond HTTPS itself.
//
// Actual security measures:
// 1. HTTPS encrypts all data in transit
// 2. Backend processes data in memory only (never written to disk)
// 3. All data is cleared immediately after analysis completes
// 4. No user accounts or persistent storage
