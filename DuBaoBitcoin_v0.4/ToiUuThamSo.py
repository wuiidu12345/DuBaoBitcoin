import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping
from sklearn.metrics import mean_squared_error

# 1. Chuẩn bị dữ liệu (Lấy 3 năm cho chắc)
DuLieuGoc = yf.download("BTC-USD", start="2021-01-01")
DuLieuGia = DuLieuGoc[["Close"]].values
BoChuanHoaGoc = MinMaxScaler(feature_range=(0, 1))
DuLieuChuanHoa = BoChuanHoaGoc.fit_transform(DuLieuGia)

# 2. Định nghĩa các "nút vặn" (Hyperparameters) để thử nghiệm
# Tui chọn các mức phổ biến nhất để bạn không bị tốn quá nhiều thời gian
KhungThamSo = {
    "units": [50, 100],  # Số nơ-ron
    "learning_rate": [0.001, 0.01],  # Tốc độ học
    "lookback": [30, 60],  # Số ngày quá khứ
}

DanhSachKetQua = []

print("--- Bắt đầu quá trình Tuning (Nêm nếm mô hình) ---")

for SoNoRon in KhungThamSo["units"]:
    for TocDoHoc in KhungThamSo["learning_rate"]:
        for ThoiGianQuanSat in KhungThamSo["lookback"]:
            print(
                f"Đang thử: Units={SoNoRon}, LR={TocDoHoc}, Lookback={ThoiGianQuanSat}..."
            )

            # Tạo tập train/test theo lookback hiện tại
            Xuan, Y = [], []
            for Buoc in range(ThoiGianQuanSat, len(DuLieuChuanHoa)):
                Xuan.append(DuLieuChuanHoa[Buoc - ThoiGianQuanSat : Buoc, 0])
                Y.append(DuLieuChuanHoa[Buoc, 0])

            Xuan, Y = np.array(Xuan), np.array(Y)

            # Chia tập
            KichThuocHuanLuyen = int(len(Xuan) * 0.8)
            XuanHuanLuyen, XuanKiemTra = (
                Xuan[:KichThuocHuanLuyen],
                Xuan[KichThuocHuanLuyen:],
            )
            YHuanLuyen, YKiemTra = Y[:KichThuocHuanLuyen], Y[KichThuocHuanLuyen:]

            # Chuẩn hóa
            BoChuanHoaXuan = MinMaxScaler(feature_range=(0, 1))
            BoChuanHoaY = MinMaxScaler(feature_range=(0, 1))

            # Reshape để scaler làm việc (phẳng hóa)
            XuanHuanLuyen = BoChuanHoaXuan.fit_transform(
                XuanHuanLuyen.reshape(-1, ThoiGianQuanSat)
            ).reshape(-1, ThoiGianQuanSat, 1)
            XuanKiemTra = BoChuanHoaXuan.transform(
                XuanKiemTra.reshape(-1, ThoiGianQuanSat)
            ).reshape(-1, ThoiGianQuanSat, 1)
            YHuanLuyen = BoChuanHoaY.fit_transform(YHuanLuyen.reshape(-1, 1))
            YKiemTra = BoChuanHoaY.transform(YKiemTra.reshape(-1, 1))

            # Xây dựng model với thông số đang thử
            MoHinhLstm = Sequential(
                [
                    LSTM(
                        SoNoRon, return_sequences=True, input_shape=(ThoiGianQuanSat, 1)
                    ),
                    Dropout(0.2),
                    LSTM(SoNoRon),
                    Dense(1),
                ]
            )
            MoHinhLstm.compile(optimizer=Adam(learning_rate=TocDoHoc), loss="mse")
            # Định nghĩa EarlyStopping mới cho mỗi lần chạy
            DungSom = EarlyStopping(
                monitor="val_loss", patience=10, restore_best_weights=True
            )
            # Train nhanh (100 epochs) để khảo sát
            MoHinhLstm.fit(
                XuanHuanLuyen,
                YHuanLuyen,
                epochs=100,
                batch_size=32,
                validation_data=(XuanKiemTra, YKiemTra),
                callbacks=[DungSom],
                verbose=0,
            )

            # Dự báo và tính lỗi
            DuBao = MoHinhLstm.predict(XuanKiemTra)
            # Nghịch đảo scale để tính RMSE trên giá USD thật (thuyết phục hơn)
            DuBaoUsd = BoChuanHoaY.inverse_transform(DuBao)
            YKiemTraUsd = BoChuanHoaY.inverse_transform(YKiemTra)

            SaiSoRmse = np.sqrt(mean_squared_error(YKiemTraUsd, DuBaoUsd))
            print(f"Hoàn tất! RMSE: {SaiSoRmse:.2f} USD")
            DanhSachKetQua.append(
                {
                    "units": SoNoRon,
                    "lr": TocDoHoc,
                    "lookback": ThoiGianQuanSat,
                    "rmse": SaiSoRmse,
                }
            )

# 3. Xuất kết quả
BaoCaoDf = pd.DataFrame(DanhSachKetQua).sort_values(by="rmse")
print("\n--- KẾT QUẢ SO SÁNH ---")
print(BaoCaoDf)
print(f"\n=> Bộ thông số tốt nhất là: \n{BaoCaoDf.iloc[0]}")
BaoCaoDf.to_csv("tuning_results.csv", index=False)
