import http from 'k6/http';
import { check, sleep } from 'k6';

// Metrik Simulasi: 50 Request bersamaan selama 15 detik
export const options = {
  vus: 50,
  duration: '15s',
};

export default function () {
  // Target port 8001 dan endpoint /ask sesuai kode FastAPI
  const url = 'http://localhost:8001/ask'; 
  
  // Menyesuaikan dengan skema QueryRequest di main.py
  const payload = JSON.stringify({
    query: "Tolong ekstrak data tagihan B2B dari klien Acme Corp bulan ini.",
    department: "finance",
    callback_url: "http://localhost:5678/webhook-test" // Simulasi webhook balikan ke n8n
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      // PENTING: Ganti nilai ini dengan API Key asli yang ada di file .env Anda
      'X-API-Key': 'b2b-super-secret-key-2026', 
    },
  };

  const res = http.post(url, payload, params);

  // Kriteria Sukses Arsitektur Asinkron:
  // Kode main.py secara eksplisit mengembalikan status_code=202 (Accepted)
  check(res, {
    'Status transaksi sukses (202 Accepted)': (r) => r.status === 202,
    'Latensi API Gateway di bawah 200ms': (r) => r.timings.duration < 200,
  });

  sleep(1);
}