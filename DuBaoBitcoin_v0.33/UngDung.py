import os

# Cấu hình chạy định tính phần cứng GPU
os.environ["TF_DETERMINISTIC_OPS"] = "1"
os.environ["TF_CUDNN_DETERMINISTIC"] = "1"

import importlib
import subprocess
import sys
from datetime import datetime, timedelta

# Ánh xạ các gói thư viện cần thiết
GoiDenMoDun = {
    "streamlit": "streamlit",
    "pandas": "pandas",
    "numpy": "numpy",
    "yfinance": "yfinance",
    "matplotlib": "matplotlib",
    "scikit-learn": "sklearn",
    "keras": "keras",
    "statsmodels": "statsmodels",
    "openpyxl": "openpyxl",
    "scipy": "scipy",
}

# Kiểm tra cài đặt thư viện còn thiếu
GoiBiThieu = []
for Goi, TenMoDun in GoiDenMoDun.items():
    try:
        importlib.import_module(TenMoDun)
    except ImportError:
        GoiBiThieu.append(Goi)

if GoiBiThieu:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *GoiBiThieu])
    except subprocess.CalledProcessError:
        print("Không thể cài các package tự động:", GoiBiThieu, file=sys.stderr)

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from keras.models import Sequential
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping, ReduceLROnPlateau
from keras.layers import (
    LSTM,
    Dense,
    Dropout,
    BatchNormalization,
    Input,
    Conv1D,
    MaxPooling1D,
    GRU,
    Bidirectional,
)
from statsmodels.tsa.arima.model import ARIMA
import random
import tensorflow as tf

# Khởi tạo cố định hạt giống ngẫu nhiên toàn cục
GiaTriSeed = 42
random.seed(GiaTriSeed)
np.random.seed(GiaTriSeed)
tf.random.set_seed(GiaTriSeed)
tf.config.experimental.enable_op_determinism()

# ========================================================================================================================
# CẤU HÌNH GIAO DIỆN & THAM SỐ ĐẦU VÀO

st.set_page_config(page_title="Dự báo giá BTC", layout="wide")
st.title("DỰ BÁO GIÁ BITCOIN")
st.sidebar.header("Cấu hình thực nghiệm")
MaGiaoDich = st.sidebar.text_input("Mã giao dịch", "BTC-USD")
TyLeHuanLuyen = st.sidebar.slider("Tỷ lệ Training (%)", 50, 90, 80) / 100

# ========================================================================================================================
# THU THẬP & XỬ LÝ DỮ LIỆU ĐA BIẾN

# Tải dữ liệu từ API Yahoo Finance
DuLieu = yf.download(MaGiaoDich, start="2023-01-01")

# ------------------------------------------------------------------------------------------------------------------------
# Tính toán các chỉ báo kỹ thuật tài chính

# Chỉ báo RSI
ChenhLech = DuLieu["Close"].diff()
Tang = ChenhLech.clip(lower=0)
Giam = -ChenhLech.clip(upper=0)
TrungBinhTang = Tang.ewm(com=13, adjust=False).mean()
TrungBinhGiam = Giam.ewm(com=13, adjust=False).mean()
Rs = TrungBinhTang / TrungBinhGiam
DuLieu["RSI"] = 100 - (100 / (1 + Rs))

# Chỉ báo MACD
DuLieu["EMA12"] = DuLieu["Close"].ewm(span=12, adjust=False).mean()
DuLieu["EMA26"] = DuLieu["Close"].ewm(span=26, adjust=False).mean()
DuLieu["MACD"] = DuLieu["EMA12"] - DuLieu["EMA26"]

# Chỉ báo Bollinger Bands
DuLieu["MA20"] = DuLieu["Close"].rolling(window=20).mean()
DuLieu["STD20"] = DuLieu["Close"].rolling(window=20).std()
DuLieu["BB_Upper"] = DuLieu["MA20"] + (2 * DuLieu["STD20"])
DuLieu["BB_Lower"] = DuLieu["MA20"] - (2 * DuLieu["STD20"])

# ------------------------------------------------------------------------------------------------------------------------
# Làm sạch và trích xuất ma trận thuộc tính

DuLieu = DuLieu.dropna()
DanhSachTinhTrang = ["Close", "RSI", "MACD", "BB_Upper", "BB_Lower"]
DuLieuDaBien = DuLieu[DanhSachTinhTrang]

# Khử tính trễ, biến đổi sai phân dữ liệu đa biến
DuLieuDaBienDiff = DuLieuDaBien.diff().dropna()

# ========================================================================================================================
# CHỨC NĂNG XUẤT FILE EXCEL CHO DỮ LIỆU THÔ

SoDongHienThi = st.sidebar.slider("Số dòng dữ liệu hiển thị", 5, 100, 10)
XuatExcel = st.sidebar.button(" Xuất dữ liệu hiện tại ra Excel")

if XuatExcel:
    ThuMucLuu = "DuLieuXuat"
    os.makedirs(ThuMucLuu, exist_ok=True)

    ThoiGianHienTai = datetime.now().strftime("%Y%m%d_%H%M%S")
    TenFileChinh = f"{MaGiaoDich.replace('/', '_')}_raw_data_{ThoiGianHienTai}.xlsx"
    DuongDanXuat = os.path.join(ThuMucLuu, TenFileChinh)

    with pd.ExcelWriter(DuongDanXuat, engine="openpyxl") as GhiExcel:
        DuLieu.to_excel(GhiExcel, sheet_name="Full Data")
        DuLieuDaBien.to_excel(GhiExcel, sheet_name="Close Price")
    st.success(f" Dữ liệu đã xuất ra file: {DuongDanXuat}")

# ========================================================================================================================
# HIỂN THỊ THÀNH PHẦN DỮ LIỆU LÊN GIAO DIỆN

st.subheader("TẬP DỮ LIỆU THỰC NGHIỆM")
Cot1, Cot2 = st.columns([1, 2])

with Cot1:
    st.write("Dữ liệu mới nhất:")
    st.write(DuLieu.tail(SoDongHienThi))

with Cot2:
    st.write("Biểu đồ giá lịch sử:")
    st.line_chart(DuLieu["Close"])

# ========================================================================================================================
# GIAO DIỆN CHỌN NGÀY DỰ BÁO TƯƠNG LAI

st.write("---")
st.subheader("DỰ BÁO TƯƠNG LAI")

NgayCuoiCung = DuLieu.index[-1].to_pydatetime()
NgayGoiY = NgayCuoiCung + timedelta(days=7)

NgayDuBaoTuongLai = st.date_input(
    "Chọn ngày muốn dự báo đến trong tương lai:",
    value=NgayGoiY,
    min_value=NgayCuoiCung + timedelta(days=1)
)

# Tính số ngày cần dự báo thêm vào tương lai
SoNgayTuongLai = (NgayDuBaoTuongLai - NgayCuoiCung.date()).days

# ========================================================================================================================
# CHẠY THỰC NGHIỆM & HUẤN LUYỆN CÁC MÔ HÌNH

if st.button(" Chạy thực nghiệm so sánh & Dự báo tương lai"):

    from keras.backend import clear_session
    clear_session()

    # --------------------------------------------------------------------------------------------------------------------
    # Phân chia dữ liệu Train và Test cho thực nghiệm

    KichThuocHuanLuyen = int(len(DuLieuDaBienDiff) * TyLeHuanLuyen)
    DuLieuHuanLuyen = DuLieuDaBienDiff[:KichThuocHuanLuyen]
    DuLieuKiemTra = DuLieuDaBienDiff[KichThuocHuanLuyen:]

    st.info(
        f"Đang huấn luyện trên {len(DuLieuHuanLuyen)} mẫu, kiểm tra trên {len(DuLieuKiemTra)} mẫu và dự báo thêm {SoNgayTuongLai} ngày tương lai..."
    )

    # Khởi tạo danh sách mốc thời gian hiển thị mở rộng
    IndexThoiGianTest = DuLieu.index[-len(DuLieuKiemTra):]
    IndexThoiGianTuongLai = [IndexThoiGianTest[-1] + timedelta(days=i) for i in range(1, SoNgayTuongLai + 1)]
    IndexThoiGianMoRong = IndexThoiGianTest.append(pd.DatetimeIndex(IndexThoiGianTuongLai))

    # --------------------------------------------------------------------------------------------------------------------
    # Cấu hình huấn luyện và dự báo đệ quy ARIMA

    with st.spinner("Đang chạy mô hình ARIMA ..."):
        # Thực nghiệm quá khứ
        LichSu = [GiaTri[0] for GiaTri in DuLieuHuanLuyen.values]
        DuBaoArima = []

        DongGocBatDau = len(DuLieuDaBien) - len(DuLieuKiemTra) - 1
        GiaGocNgayTruoc = DuLieuDaBien["Close"].values[DongGocBatDau]

        for Buoc in range(len(DuLieuKiemTra)):
            MoHinhArima = ARIMA(LichSu, order=(5, 0, 0))
            KetQuaArima = MoHinhArima.fit()
            DuBaoDiff = KetQuaArima.forecast()[0]

            GiaUsdDuBao = GiaGocNgayTruoc + DuBaoDiff
            DuBaoArima.append(GiaUsdDuBao)

            LichSu.append(DuBaoDiff)
            GiaGocNgayTruoc = GiaUsdDuBao

        # Dự báo tương lai
        DuBaoArimaTuongLai = list(DuBaoArima)
        LichSuTuongLai = list(LichSu)
        GiaGocNgayTruocTuongLai = GiaGocNgayTruoc

        for Buoc in range(SoNgayTuongLai):
            MoHinhArima = ARIMA(LichSuTuongLai, order=(5, 0, 0))
            KetQuaArima = MoHinhArima.fit()
            DuBaoDiff = KetQuaArima.forecast()[0]

            GiaUsdDuBao = GiaGocNgayTruocTuongLai + DuBaoDiff
            DuBaoArimaTuongLai.append(GiaUsdDuBao)

            LichSuTuongLai.append(DuBaoDiff)
            GiaGocNgayTruocTuongLai = GiaUsdDuBao

    # --------------------------------------------------------------------------------------------------------------------
    # Chuẩn bị dữ liệu cho các mô hình học sâu (LSTM, GRU, BiLSTM)

    BoChuanHoa = MinMaxScaler(feature_range=(0, 1))
    DuLieuHuanLuyenChuanHoa = BoChuanHoa.fit_transform(DuLieuHuanLuyen)

    ThoiGianQuanSat = 30
    TocDoHocToiUu = 0.001

    XuanHuanLuyen, YHuanLuyen = [], []
    for Buoc in range(ThoiGianQuanSat, len(DuLieuHuanLuyenChuanHoa)):
        XuanHuanLuyen.append(DuLieuHuanLuyenChuanHoa[Buoc - ThoiGianQuanSat : Buoc, :])
        YHuanLuyen.append(DuLieuHuanLuyenChuanHoa[Buoc, 0])

    XuanHuanLuyen, YHuanLuyen = np.array(XuanHuanLuyen), np.array(YHuanLuyen)

    ToanBoDuLieu = pd.concat((DuLieuHuanLuyen, DuLieuKiemTra), axis=0)
    NgayBatDauTest = len(ToanBoDuLieu) - len(DuLieuKiemTra) - ThoiGianQuanSat
    DauVao = ToanBoDuLieu[NgayBatDauTest:].values
    DauVaoChuanHoa = BoChuanHoa.transform(DauVao)

    XuanKiemTra = []
    for Buoc in range(ThoiGianQuanSat, len(DauVaoChuanHoa)):
        XuanKiemTra.append(DauVaoChuanHoa[Buoc - ThoiGianQuanSat : Buoc, :])
    XuanKiemTra = np.array(XuanKiemTra)

    DongBatDau = len(DuLieuDaBien) - len(DuLieuKiemTra) - 1
    DongKetThuc = len(DuLieuDaBien) - 1
    GiaNgayTruocDo = DuLieuDaBien["Close"].values[DongBatDau:DongKetThuc].flatten()

    DungSom = EarlyStopping(monitor="val_loss", patience=12, restore_best_weights=True)
    GiamTocDoHoc = ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=4, min_lr=0.00001, verbose=0)

    # Hàm hỗ trợ dự báo đệ quy tương lai cho mạng Neural
    def DuBaoDeQuyDeepLearning(model, danh_sach_cuoi_cung_diff, gia_goc_cuoi, so_buoc):
        DanhSachChuanHoa = list(danh_sach_cuoi_cung_diff)
        KetQuaGiaThuc = []
        GiaHienTai = gia_goc_cuoi

        for _ in range(so_buoc):
            CuaSoVao = np.array(DanhSachChuanHoa[-ThoiGianQuanSat:])
            CuaSoVao = np.reshape(CuaSoVao, (1, ThoiGianQuanSat, 5))
            
            DuBaoRaw = model.predict(CuaSoVao, verbose=0)
            
            KhungGiaLap = np.zeros((1, 5))
            KhungGiaLap[0, 0] = DuBaoRaw[0, 0]
            DuBaoDiff = BoChuanHoa.inverse_transform(KhungGiaLap)[0, 0]
            
            GiaHienTai = GiaHienTai + DuBaoDiff
            KetQuaGiaThuc.append(GiaHienTai)
            
            MoRongChuanHoa = np.zeros((1, 5))
            MoRongChuanHoa[0, 0] = DuBaoRaw[0, 0] 
            DanhSachChuanHoa.append(MoRongChuanHoa[0])
            
        return KetQuaGiaThuc

    # --------------------------------------------------------------------------------------------------------------------
    # Cấu hình huấn luyện mạng lai CNN-LSTM

    with st.spinner("Đang huấn luyện mô hình LSTM ..."):
        MoHinhLstm = Sequential([
            Input(shape=(ThoiGianQuanSat, 5)),
            Conv1D(filters=32, kernel_size=3, activation="relu", padding="same"),
            MaxPooling1D(pool_size=2),
            BatchNormalization(),
            Dropout(0.15),
            LSTM(64),
            BatchNormalization(),
            Dropout(0.15),
            Dense(16, activation="relu"),
            Dense(1),
        ])

        MoHinhLstm.compile(optimizer=Adam(learning_rate=TocDoHocToiUu), loss="mean_squared_error")
        LichSuLstm = MoHinhLstm.fit(
            XuanHuanLuyen, YHuanLuyen, epochs=200, batch_size=32,
            validation_split=0.176, shuffle=False, callbacks=[DungSom, GiamTocDoHoc], verbose=0,
        )

        # Thực nghiệm quá khứ
        DuBaoLstmRaw = MoHinhLstm.predict(XuanKiemTra)
        KhungGiaLap = np.zeros((len(DuBaoLstmRaw), 5))
        KhungGiaLap[:, 0] = DuBaoLstmRaw.flatten()
        DuBaoLstmDiff = BoChuanHoa.inverse_transform(KhungGiaLap)[:, 0]
        DuBaoLstm = GiaNgayTruocDo + DuBaoLstmDiff.flatten()

        # Dự báo tương lai
        DuBaoLstmTuongLai = DuBaoDeQuyDeepLearning(
            MoHinhLstm, DauVaoChuanHoa[-ThoiGianQuanSat:], DuLieuDaBien["Close"].values[-1], SoNgayTuongLai
        )
        DuBaoLstmMoRong = np.concatenate([np.array(DuBaoLstm).flatten(), np.array(DuBaoLstmTuongLai).flatten()])

    # --------------------------------------------------------------------------------------------------------------------
    # Cấu hình huấn luyện mạng GRU thuần

    with st.spinner("Đang huấn luyện mô hình đối chứng GRU ..."):
        clear_session()
        tf.random.set_seed(GiaTriSeed)

        MoHinhGru = Sequential([
            Input(shape=(ThoiGianQuanSat, 5)),
            GRU(64, kernel_initializer=tf.keras.initializers.GlorotUniform(seed=GiaTriSeed)),
            BatchNormalization(),
            Dropout(0.15),
            Dense(8, activation="relu", kernel_initializer=tf.keras.initializers.GlorotUniform(seed=GiaTriSeed)),
            Dense(1, kernel_initializer=tf.keras.initializers.GlorotUniform(seed=GiaTriSeed)),
        ])
        MoHinhGru.compile(optimizer=Adam(learning_rate=TocDoHocToiUu), loss="mean_squared_error")
        MoHinhGru.fit(
            XuanHuanLuyen, YHuanLuyen, epochs=100, batch_size=32,
            validation_split=0.176, shuffle=False, callbacks=[DungSom, GiamTocDoHoc], verbose=0,
        )

        # Thực nghiệm quá khứ
        DuBaoGruRaw = MoHinhGru.predict(XuanKiemTra)
        KhungGru = np.zeros((len(DuBaoGruRaw), 5))
        KhungGru[:, 0] = DuBaoGruRaw.flatten()
        DuBaoGruDiff = BoChuanHoa.inverse_transform(KhungGru)[:, 0]
        DuBaoGru = GiaNgayTruocDo + DuBaoGruDiff.flatten()

        # Dự báo tương lai
        DuBaoGruTuongLai = DuBaoDeQuyDeepLearning(
            MoHinhGru, DauVaoChuanHoa[-ThoiGianQuanSat:], DuLieuDaBien["Close"].values[-1], SoNgayTuongLai
        )
        DuBaoGruMoRong = np.concatenate([np.array(DuBaoGru).flatten(), np.array(DuBaoGruTuongLai).flatten()])

    # --------------------------------------------------------------------------------------------------------------------
    # Cấu hình huấn luyện mạng BiLSTM hai chiều

    with st.spinner("Đang huấn luyện mô hình đối chứng BiLSTM ..."):
        clear_session()
        tf.random.set_seed(GiaTriSeed)

        MoHinhBiLstm = Sequential([
            Input(shape=(ThoiGianQuanSat, 5)),
            Bidirectional(LSTM(64, kernel_initializer=tf.keras.initializers.GlorotUniform(seed=GiaTriSeed))),
            BatchNormalization(),
            Dropout(0.15),
            Dense(16, activation="relu", kernel_initializer=tf.keras.initializers.GlorotUniform(seed=GiaTriSeed)),
            Dense(1, kernel_initializer=tf.keras.initializers.GlorotUniform(seed=GiaTriSeed)),
        ])
        MoHinhBiLstm.compile(optimizer=Adam(learning_rate=TocDoHocToiUu), loss="mean_squared_error")
        MoHinhBiLstm.fit(
            XuanHuanLuyen, YHuanLuyen, epochs=100, batch_size=32,
            validation_split=0.176, shuffle=False, callbacks=[DungSom, GiamTocDoHoc], verbose=0,
        )

        # Thực nghiệm quá khứ
        DuBaoBiLstmRaw = MoHinhBiLstm.predict(XuanKiemTra)
        KhungBiLstm = np.zeros((len(DuBaoBiLstmRaw), 5))
        KhungBiLstm[:, 0] = DuBaoBiLstmRaw.flatten()
        DuBaoBiLstmDiff = BoChuanHoa.inverse_transform(KhungBiLstm)[:, 0]
        DuBaoBiLstm = GiaNgayTruocDo + DuBaoBiLstmDiff.flatten()

        # Dự báo tương lai
        DuBaoBiLstmTuongLai = DuBaoDeQuyDeepLearning(
            MoHinhBiLstm, DauVaoChuanHoa[-ThoiGianQuanSat:], DuLieuDaBien["Close"].values[-1], SoNgayTuongLai
        )
        DuBaoBiLstmMoRong = np.concatenate([np.array(DuBaoBiLstm).flatten(), np.array(DuBaoBiLstmTuongLai).flatten()])

    # --------------------------------------------------------------------------------------------------------------------
    # Tính toán các chỉ số sai số thống kê (chỉ quá khứ)

    GiaThucTeTest = DuLieuDaBien["Close"].values[-len(DuLieuKiemTra) :].flatten()

    def LayChiSoSaiSo(y_true, y_pred):
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        return mae, rmse

    SaiSoMaeArima, SaiSoRmseArima = LayChiSoSaiSo(GiaThucTeTest, DuBaoArima)
    SaiSoMaeGru, SaiSoRmseGru = LayChiSoSaiSo(GiaThucTeTest, DuBaoGru)
    SaiSoMaeBiLstm, SaiSoRmseBiLstm = LayChiSoSaiSo(GiaThucTeTest, DuBaoBiLstm)
    SaiSoMaeLstm, SaiSoRmseLstm = LayChiSoSaiSo(GiaThucTeTest, DuBaoLstm)

    # ====================================================================================================================
    # TRỰC QUAN HÓA & ĐÁNH GIÁ HIỆU NĂNG SAI SỐ

    st.divider()
    st.subheader("ĐÁNH GIÁ VÀ SO SÁNH TỔNG QUAN")

    # --------------------------------------------------------------------------------------------------------------------
    # Biểu đồ so sánh đường giá dự báo thực nghiệm và tương lai mở rộng

    st.write("### Biểu đồ so sánh đường giá dự báo thực nghiệm & tương lai")
    BieuDoKetQua, TrucKetQua = plt.subplots(figsize=(12, 5))

    # Vẽ đường thực tế
    TrucKetQua.plot(IndexThoiGianTest, GiaThucTeTest, color="black", label="Thực tế ", linewidth=2)
    
    # Vẽ các đường mô hình chạy dài từ Quá khứ xuyên suốt qua Tương lai mở rộng
    TrucKetQua.plot(IndexThoiGianMoRong, DuBaoArimaTuongLai, color="green", label="ARIMA ", linestyle="--", alpha=0.6)
    TrucKetQua.plot(IndexThoiGianMoRong, DuBaoGruMoRong, color="purple", label="GRU ", linestyle="-.", alpha=0.7)
    TrucKetQua.plot(IndexThoiGianMoRong, DuBaoBiLstmMoRong, color="orange", label="BiLSTM ", linestyle=":", alpha=0.7)
    TrucKetQua.plot(IndexThoiGianMoRong, DuBaoLstmMoRong, color="red", label="CNN-LSTM (Đề xuất) ", linewidth=2.5)

    # Đường thẳng đứng giữa Quá khứ và Tương lai
    TrucKetQua.axvline(IndexThoiGianTest[-1], color="blue", linestyle=":", alpha=0.8, label="Bắt đầu Tương lai")

    TrucKetQua.legend()
    st.pyplot(BieuDoKetQua)
    st.divider()

    # --------------------------------------------------------------------------------------------------------------------
    # Đồ thị tán xạ tương quan tuyến tính

    st.write("### ĐỒ THỊ TÁN XẠ TƯƠNG QUAN TUYẾN TÍNH")
    CotTx1, CotTx2, CotTx3 = st.columns(3)

    MocNhoNhat = min(min(GiaThucTeTest), min(DuBaoLstm), min(DuBaoGru), min(DuBaoBiLstm))
    MocLonNhat = max(max(GiaThucTeTest), max(DuBaoLstm), max(DuBaoGru), max(DuBaoBiLstm))
    DuongLyTuong = [MocNhoNhat, MocLonNhat]

    with CotTx1:
        st.write("#### Mô hình đề xuất CNN-LSTM")
        BieuDoTx1, TrucTx1 = plt.subplots(figsize=(5, 5))
        TrucTx1.scatter(GiaThucTeTest, DuBaoLstm, color="red", alpha=0.5, edgecolors="none")
        TrucTx1.plot(DuongLyTuong, DuongLyTuong, color="black", linestyle="--")
        TrucTx1.set_xlabel("Giá thực tế (USD)")
        TrucTx1.set_ylabel("Giá dự báo (USD)")
        st.pyplot(BieuDoTx1)

    with CotTx2:
        st.write("#### Mô hình đối chứng GRU")
        BieuDoTx2, TrucTx2 = plt.subplots(figsize=(5, 5))
        TrucTx2.scatter(GiaThucTeTest, DuBaoGru, color="purple", alpha=0.5, edgecolors="none")
        TrucTx2.plot(DuongLyTuong, DuongLyTuong, color="black", linestyle="--")
        TrucTx2.set_xlabel("Giá thực tế (USD)")
        TrucTx2.set_ylabel("Giá dự báo (USD)")
        st.pyplot(BieuDoTx2)

    with CotTx3:
        st.write("#### Mô hình đối chứng BiLSTM")
        BieuDoTx3, TrucTx3 = plt.subplots(figsize=(5, 5))
        TrucTx3.scatter(GiaThucTeTest, DuBaoBiLstm, color="orange", alpha=0.5, edgecolors="none")
        TrucTx3.plot(DuongLyTuong, DuongLyTuong, color="black", linestyle="--")
        TrucTx3.set_xlabel("Giá thực tế (USD)")
        TrucTx3.set_ylabel("Giá dự báo (USD)")
        st.pyplot(BieuDoTx3)

    st.divider()

    # --------------------------------------------------------------------------------------------------------------------
    # Đồ thị chẩn đoán nội tại mô hình đề xuất CNN-LSTM

    st.write("### ĐỒ THỊ CHUẨN ĐOÁN NỘI TẠI MÔ HÌNH ĐỀ XUẤT CNN-LSTM")
    CotDeXuat1, CotDeXuat2 = st.columns([1, 1])

    with CotDeXuat1:
        st.write("#### Đồ thị hội tụ hàm mất mát")
        BieuDoMatMat, TrucMatMat = plt.subplots(figsize=(5, 3.5))
        TrucMatMat.plot(LichSuLstm.history["loss"], label="Train Loss", color="blue")
        TrucMatMat.plot(LichSuLstm.history["val_loss"], label="Validation Loss", color="orange")
        TrucMatMat.set_xlabel("Epochs")
        TrucMatMat.set_ylabel("Loss (MSE)")
        TrucMatMat.legend()
        st.pyplot(BieuDoMatMat)

    with CotDeXuat2:
        st.write("#### Đồ thị phân phối tần suất sai số")
        SaiSoDuBao = GiaThucTeTest - DuBaoLstm
        BieuDoPhanPhoi, TrucPhanPhoi = plt.subplots(figsize=(5, 3.5))

        SoLuongCot = 30
        TầnSuất, Thùng, VaCh = TrucPhanPhoi.hist(
            SaiSoDuBao, bins=SoLuongCot, color="red", alpha=0.6, edgecolor="white", density=True, label="Mật độ thực tế"
        )

        from scipy.stats import norm
        GiaTriTrungBinh, DoLechChuan = norm.fit(SaiSoDuBao)
        DuongBienX = np.linspace(min(SaiSoDuBao), max(SaiSoDuBao), 100)
        DuongBienY = norm.pdf(DuongBienX, GiaTriTrungBinh, DoLechChuan)

        TrucPhanPhoi.plot(DuongBienX, DuongBienY, color="black", linestyle="--", linewidth=1.5, label="Đường phân phối chuẩn")
        TrucPhanPhoi.axvline(0, color="blue", linestyle="-", linewidth=1.5, label="Mốc sai số bằng 0")
        TrucPhanPhoi.set_xlabel("Biên độ sai số (USD)")
        TrucPhanPhoi.set_ylabel("Mật độ tần suất")
        TrucPhanPhoi.legend(fontsize="small")
        TrucPhanPhoi.grid(True, linestyle=":", alpha=0.5)
        st.pyplot(BieuDoPhanPhoi)

    st.divider()

    # --------------------------------------------------------------------------------------------------------------------
    # Bảng tổng kết sai số thực nghiệm định lượng

    st.write("### Bảng tổng kết sai số thực nghiệm (đơn vị: USD)")
    BangSoSanhDf = pd.DataFrame({
        "Mô hình": ["ARIMA ", "GRU ", "BiLSTM ", "CNN-LSTM (Đề xuất) "],
        "MAE": [f"{SaiSoMaeArima:.2f}", f"{SaiSoMaeGru:.2f}", f"{SaiSoMaeBiLstm:.2f}", f"{SaiSoMaeLstm:.2f}"],
        "RMSE": [f"{SaiSoRmseArima:.2f}", f"{SaiSoRmseGru:.2f}", f"{SaiSoRmseBiLstm:.2f}", f"{SaiSoRmseLstm:.2f}"],
    })
    st.table(BangSoSanhDf)

    # --------------------------------------------------------------------------------------------------------------------
    # Đồng bộ hóa bộ nhớ Session State

    st.session_state["TrangThaiKetQuaDf"] = pd.DataFrame({
        "Date": IndexThoiGianMoRong,
        "ARIMA": np.array(DuBaoArimaTuongLai).flatten(),
        "GRU": np.array(DuBaoGruMoRong).flatten(),
        "BiLSTM": np.array(DuBaoBiLstmMoRong).flatten(),
        "CNN-LSTM": np.array(DuBaoLstmMoRong).flatten(),
    })
    st.success("Thực nghiệm và dự báo tương lai hoàn tất!")

# ========================================================================================================================
# XUẤT FILE EXCEL CHO KẾT QUẢ DỰ BÁO

if "TrangThaiKetQuaDf" in st.session_state:
    if st.button("📥 Xuất kết quả dự báo & Sai số ra Excel"):
        ThuMucLuu = "KetQuaDuBao"
        os.makedirs(ThuMucLuu, exist_ok=True)

        ThoiGianHienTai = datetime.now().strftime("%Y%m%d_%H%M%S")
        TenFileChinh = f"{MaGiaoDich.replace('/', '_')}_results_{ThoiGianHienTai}.xlsx"
        DuongDanXuat = os.path.join(ThuMucLuu, TenFileChinh)

        with pd.ExcelWriter(DuongDanXuat, engine="openpyxl") as GhiExcel:
            st.session_state["TrangThaiKetQuaDf"].to_excel(GhiExcel, sheet_name="Predictions", index=False)
        st.success(f"Đã lưu kết quả vào file: {DuongDanXuat}")

# ========================================================================================================================
