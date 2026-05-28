import importlib
import subprocess
import sys

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
}

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
from keras.layers import LSTM, Dense, Dropout
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping
from statsmodels.tsa.arima.model import ARIMA

st.set_page_config(page_title="Đồ án Dự báo BTC", layout="wide")
st.title(" Thực nghiệm Dự báo giá Bitcoin: LSTM vs ARIMA")

# --- 4.1. THIẾT LẬP MÔI TRƯỜNG & DỮ LIỆU ---
st.sidebar.header("Cấu hình thực nghiệm")
MaGiaoDich = st.sidebar.text_input("Mã giao dịch", "BTC-USD")
TyLeHuanLuyen = st.sidebar.slider("Tỷ lệ Training (%)", 50, 90, 80) / 100

# Tải dữ liệu
DuLieu = yf.download(MaGiaoDich, start="2023-01-01")
GiaDongCua = DuLieu[["Close"]]
SoDongHienThi = st.sidebar.slider("Số dòng dữ liệu hiển thị", 5, 100, 10)
XuatExcel = st.sidebar.button(" Xuất dữ liệu hiện tại ra Excel")

if XuatExcel:
    DuongDanXuat = f"{MaGiaoDich.replace('/', '_')}_raw_data.xlsx"
    with pd.ExcelWriter(DuongDanXuat, engine="openpyxl") as GhiExcel:
        DuLieu.to_excel(GhiExcel, sheet_name="Full Data")
        GiaDongCua.to_excel(GhiExcel, sheet_name="Close Price")
    st.success(f" Dữ liệu đã xuất ra file: {DuongDanXuat}")

st.subheader("4.1. Tập dữ liệu thực nghiệm")
Cot1, Cot2 = st.columns([1, 2])
with Cot1:
    st.write("Dữ liệu mới nhất:")
    st.write(DuLieu.tail(SoDongHienThi))
with Cot2:
    st.write("Biểu đồ giá lịch sử:")
    st.line_chart(DuLieu["Close"])

if st.button(" Chạy thực nghiệm so sánh"):
    # 1. Chia dữ liệu
    KichThuocHuanLuyen = int(len(GiaDongCua) * TyLeHuanLuyen)
    DuLieuHuanLuyen = GiaDongCua[:KichThuocHuanLuyen]
    DuLieuKiemTra = GiaDongCua[KichThuocHuanLuyen:]

    st.info(
        f"Đang huấn luyện trên {len(DuLieuHuanLuyen)} mẫu và kiểm tra trên {len(DuLieuKiemTra)} mẫu..."
    )

    # --- 4.2. MÔ HÌNH CƠ SỞ ARIMA ---
    with st.spinner("Đang chạy mô hình ARIMA ..."):
        LichSu = [GiaTri for GiaTri in DuLieuHuanLuyen.values]
        DuBaoArima = []
        for Buoc in range(len(DuLieuKiemTra)):
            MoHinhArima = ARIMA(LichSu, order=(5, 1, 0))
            KetQuaArima = MoHinhArima.fit()
            DuBaoArima.append(KetQuaArima.forecast()[0])
            LichSu.append(DuLieuKiemTra.values[Buoc])

    #  4.3. MÔ HÌNH ĐỀ XUẤT LSTM
    with st.spinner("Đang huấn luyện mô hình LSTM ..."):
        # Chuẩn hóa
        BoChuanHoa = MinMaxScaler(feature_range=(0, 1))
        DuLieuHuanLuyenChuanHoa = BoChuanHoa.fit_transform(DuLieuHuanLuyen)

        # Cấu hình theo kết quả tinh chỉnh tốt nhất
        ThoiGianQuanSat = 30  #  15  ngày
        SoNoRonToiUu = 100  #  100  nơ ron
        TocDoHocToiUu = 0.001  # Tốc độ học

        XuanHuanLuyen, YHuanLuyen = [], []
        for Buoc in range(ThoiGianQuanSat, len(DuLieuHuanLuyenChuanHoa)):
            XuanHuanLuyen.append(
                DuLieuHuanLuyenChuanHoa[Buoc - ThoiGianQuanSat : Buoc, 0]
            )
            YHuanLuyen.append(DuLieuHuanLuyenChuanHoa[Buoc, 0])

        XuanHuanLuyen, YHuanLuyen = np.array(XuanHuanLuyen), np.array(YHuanLuyen)
        XuanHuanLuyen = np.reshape(
            XuanHuanLuyen, (XuanHuanLuyen.shape[0], XuanHuanLuyen.shape[1], 1)
        )

        # Kiến trúc mô hình
        MoHinhLstm = Sequential(
            [
                LSTM(
                    SoNoRonToiUu,
                    return_sequences=True,
                    input_shape=(ThoiGianQuanSat, 1),
                ),
                Dropout(0.2),
                LSTM(SoNoRonToiUu),
                Dropout(0.2),
                Dense(1),
            ]
        )

        MoHinhLstm.compile(
            optimizer=Adam(learning_rate=TocDoHocToiUu), loss="mean_squared_error"
        )

        # Định nghĩa EarlyStopping để dừng khi đạt độ chính xác tốt nhất
        DungSom = EarlyStopping(
            monitor="val_loss", patience=10, restore_best_weights=True
        )

        LichSuLstm = MoHinhLstm.fit(
            XuanHuanLuyen,
            YHuanLuyen,
            epochs=200,
            batch_size=32,
            validation_split=0.176,  # 17.6%  tinh chỉnh
            callbacks=[DungSom],
            verbose=0,
        )

        # Dự báo LSTM trên tập Test
        ToanBoDuLieu = pd.concat((DuLieuHuanLuyen, DuLieuKiemTra), axis=0)
        DauVao = ToanBoDuLieu[
            len(ToanBoDuLieu) - len(DuLieuKiemTra) - ThoiGianQuanSat :
        ].values
        DauVao = BoChuanHoa.transform(DauVao)

        XuanKiemTra = []
        for Buoc in range(ThoiGianQuanSat, len(DauVao)):
            XuanKiemTra.append(DauVao[Buoc - ThoiGianQuanSat : Buoc, 0])
        XuanKiemTra = np.array(XuanKiemTra)
        XuanKiemTra = np.reshape(
            XuanKiemTra, (XuanKiemTra.shape[0], XuanKiemTra.shape[1], 1)
        )

        DuBaoLstm = MoHinhLstm.predict(XuanKiemTra)
        DuBaoLstm = BoChuanHoa.inverse_transform(DuBaoLstm)

    #  4.4. ĐÁNH GIÁ KẾT QUẢ
    st.divider()
    st.subheader("4.4. Đánh giá và So sánh")

    CotKetQua1, CotKetQua2 = st.columns([1, 2])

    with CotKetQua1:
        st.write(" Độ hội tụ ")
        BieuDoMatMat, TrucMatMat = plt.subplots(figsize=(5, 4))
        TrucMatMat.plot(LichSuLstm.history["loss"], label="Train Loss", color="blue")
        TrucMatMat.plot(
            LichSuLstm.history["val_loss"], label="Validation Loss", color="orange"
        )
        TrucMatMat.set_xlabel("Epochs")
        TrucMatMat.set_ylabel("Loss (MSE)")
        TrucMatMat.legend()
        st.pyplot(BieuDoMatMat)

    with CotKetQua2:
        # Tính toán sai số
        def LayChiSoSaiSo(ThucTe, DuBao):
            SaiSoTuyetDoiTrungBinh = mean_absolute_error(ThucTe, DuBao)
            CanBacHaiSaiSoTrungBinh = np.sqrt(mean_squared_error(ThucTe, DuBao))
            return SaiSoTuyetDoiTrungBinh, CanBacHaiSaiSoTrungBinh

        SaiSoMaeArima, SaiSoRmseArima = LayChiSoSaiSo(DuLieuKiemTra.values, DuBaoArima)
        SaiSoMaeLstm, SaiSoRmseLstm = LayChiSoSaiSo(DuLieuKiemTra.values, DuBaoLstm)

        st.write(" Bảng so sánh sai số (Đơn vị: USD)")
        BangSoSanhDf = pd.DataFrame(
            {
                "Mô hình": ["ARIMA ", "LSTM "],
                "MAE": [f"{SaiSoMaeArima:.2f}", f"{SaiSoMaeLstm:.2f}"],
                "RMSE": [f"{SaiSoRmseArima:.2f}", f"{SaiSoRmseLstm:.2f}"],
            }
        )
        st.table(BangSoSanhDf)

    # Biểu đồ trực quan lớn
    st.write(" Biểu đồ trực quan so sánh 3 đường giá")
    BieuDoKetQua, TrucKetQua = plt.subplots(figsize=(12, 5))
    TrucKetQua.plot(
        DuLieuKiemTra.index,
        DuLieuKiemTra.values,
        color="black",
        label="Thực tế ",
        linewidth=2,
    )
    TrucKetQua.plot(
        DuLieuKiemTra.index, DuBaoArima, color="green", label="ARIMA ", linestyle="--"
    )
    TrucKetQua.plot(
        DuLieuKiemTra.index, DuBaoLstm, color="red", label="LSTM ", linewidth=2
    )
    TrucKetQua.set_title(f"Dự báo giá {MaGiaoDich} trên tập kiểm tra")
    TrucKetQua.legend()
    st.pyplot(BieuDoKetQua)

    st.session_state["TrangThaiKetQuaDf"] = pd.DataFrame(
        {
            "Date": DuLieuKiemTra.index,
            "Actual": DuLieuKiemTra.values.flatten(),
            "ARIMA": np.array(DuBaoArima).flatten(),
            "LSTM": np.array(DuBaoLstm).flatten(),
        }
    )
    st.session_state["TrangThaiChiSo"] = [
        SaiSoMaeArima,
        SaiSoRmseArima,
        SaiSoMaeLstm,
        SaiSoRmseLstm,
    ]
    st.success(" Thực nghiệm hoàn tất! Bạn có thể xuất kết quả ở dưới.")

if "TrangThaiKetQuaDf" in st.session_state:
    if st.button("📥 Xuất kết quả dự báo & Sai số ra Excel"):
        DuongDanXuat = f"{MaGiaoDich.replace('/', '_')}_results.xlsx"
        with pd.ExcelWriter(DuongDanXuat, engine="openpyxl") as GhiExcel:
            st.session_state["TrangThaiKetQuaDf"].to_excel(
                GhiExcel, sheet_name="Predictions", index=False
            )
            # Thêm các sheet khác nếu cần...
        st.success(f" Đã lưu kết quả vào file: {DuongDanXuat}")
