from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
from dummy_data import database_risiko

app = FastAPI(
    title="API Manajemen Risiko",
    description="api buat ngelola dan nilai risiko perusahaan",
    version="1.0.0"
)

# model pydantic buat nentuin struktur balikan data dan request
class RisikoResponse(BaseModel):
    id: int = Field(..., description="id unik buat tiap risiko")
    nama_risiko: str
    deskripsi: str
    status: str
    skor: int

class RisikoListResponse(BaseModel):
    status: str
    data: List[RisikoResponse]

class RisikoSingleResponse(BaseModel):
    status: str
    data: RisikoResponse

class RisikoDeleteResponse(BaseModel):
    status: str
    data_terhapus: RisikoResponse

class ErrorResponse(BaseModel):
    detail: str

class RisikoBaru(BaseModel):
    id: int = Field(..., description="masukin id unik")
    nama_risiko: str
    deskripsi: str

class PenilaianRisiko(BaseModel):
    probabilitas: int = Field(..., ge=1, le=5, description="masukin nilai probabilitas dari 1 sampe 5")
    dampak: int = Field(..., ge=1, le=5, description="masukin nilai dampak dari 1 sampe 5")

# routing utama buat fungsi manajemen risiko

@app.get(
    "/risks", 
    response_model=RisikoListResponse, 
    tags=["Risiko"], 
    summary="ambil semua data risiko yang ada"
)
def ambil_semua_risiko():
    return {"status": "sukses", "data": database_risiko}

@app.get(
    "/risks/critical", 
    response_model=RisikoListResponse, 
    tags=["Risiko"], 
    summary="cari daftar risiko yang statusnya tinggi atau kritis",
    responses={404: {"model": ErrorResponse}}
)
def cari_risiko_kritis():
    hasil = [r for r in database_risiko if r["status"].lower() in ["tinggi", "kritis"]]
    if not hasil:
        raise HTTPException(status_code=404, detail="ngga ada risiko tingkat tinggi atau kritis yang ketemu")
    return {"status": "sukses", "data": hasil}

@app.post(
    "/risks", 
    response_model=RisikoSingleResponse, 
    tags=["Risiko"], 
    summary="tambahin data risiko baru ke database dummy",
    responses={400: {"model": ErrorResponse}}
)
def tambah_risiko(risiko: RisikoBaru):
    for r in database_risiko:
        if r["id"] == risiko.id:
            raise HTTPException(status_code=400, detail="id risiko ini udah kepake, coba pake id lain")
            
    data_baru = risiko.model_dump()
    data_baru["status"] = "belum dinilai"
    data_baru["skor"] = 0
    database_risiko.append(data_baru)
    return {"status": "sukses nambahin risiko", "data": data_baru}

@app.post(
    "/risks/assess/{id_risiko}", 
    response_model=RisikoSingleResponse, 
    tags=["Risiko"], 
    summary="hitung skor risiko dan tentuin statusnya",
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}}
)
def hitung_skor_risiko(id_risiko: int, nilai: PenilaianRisiko):
    if nilai.probabilitas < 1 or nilai.probabilitas > 5 or nilai.dampak < 1 or nilai.dampak > 5:
        raise HTTPException(status_code=400, detail="nilai probabilitas dan dampak wajib di antara 1 sampe 5")

    for risiko in database_risiko:
        if risiko["id"] == id_risiko:
            skor_akhir = nilai.probabilitas * nilai.dampak
            risiko["skor"] = skor_akhir

            if skor_akhir <= 4:
                risiko["status"] = "Rendah"
            elif skor_akhir <= 9:
                risiko["status"] = "Sedang"
            elif skor_akhir <= 14:
                risiko["status"] = "Tinggi"
            else:
                risiko["status"] = "Kritis"

            return {"status": "sukses menilai risiko", "data": risiko}

    raise HTTPException(status_code=404, detail="id risiko yang dicari ngga ketemu")

@app.put(
    "/risks/{id_risiko}/mitigate", 
    response_model=RisikoSingleResponse, 
    tags=["Risiko"], 
    summary="ubah status risiko jadi udah dimitigasi",
    responses={404: {"model": ErrorResponse}}
)
def mitigasi_risiko(id_risiko: int):
    for risiko in database_risiko:
        if risiko["id"] == id_risiko:
            risiko["status"] = "Telah Dimitigasi"
            return {"status": "sukses update mitigasi", "data": risiko}
    raise HTTPException(status_code=404, detail="id risiko yang mau diubah ngga ketemu")

@app.delete(
    "/risks/{id_risiko}", 
    response_model=RisikoDeleteResponse, 
    tags=["Risiko"], 
    summary="hapus data risiko berdasarkan id",
    responses={404: {"model": ErrorResponse}}
)
def hapus_risiko(id_risiko: int):
    for index, risiko in enumerate(database_risiko):
        if risiko["id"] == id_risiko:
            data_hapus = database_risiko.pop(index)
            return {"status": "sukses ngapus data", "data_terhapus": data_hapus}
    raise HTTPException(status_code=404, detail="id risiko yang mau dihapus ngga ketemu")

@app.get("/")
def halaman_utama():
    # nampilin buku menu daftar endpoint api
    return {
        "message": "API Manajemen Risiko Tata Kelola Perusahaan",
        "docs": "Buka /docs untuk mencoba API secara interaktif",
        "endpoints": {
            "Data Retrieval & Pencarian": [
                "GET /risks",
                "GET /risks/critical"
            ],
            "Operasi Data": [
                "POST /risks",
                "PUT /risks/{id_risiko}/mitigate",
                "DELETE /risks/{id_risiko}"
            ],
            "Komputasi": [
                "POST /risks/assess/{id_risiko}"
            ]
        }
    }