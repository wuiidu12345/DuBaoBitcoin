**🚀 ĐỒ ÁN THỰC NGHIỆM GIÁ BITCOIN**

Dự án này đã được cấu hình chạy tự động, giúp toàn bộ các thành viên trong nhóm đồng bộ môi trường ảo và thư viện chỉ với 1 cú click chuột, tránh lỗi xung đột hệ thống.

======================================================================

**📂 1. CẤU TRÚC THƯ MỤC BẮT BUỘC**

Để file cài đặt tự động `ChayUngDung.bat` hoạt động chính xác, cấu trúc thư mục của bạn bắt buộc phải được sắp xếp như sau (thư mục `miniconda_core` nằm ở thư mục cha, dùng chung cho các phiên bản code):

```
DuBaoBitcoin-main/
│
├── DuBaoBitcoin_vX.X/       <-- Folder mã nguồn dự án (Tải từ GitHub)
│   ├── UngDung.py
│   ├── ThuVien.txt
│   └── ChayUngDung.bat
│
├── miniconda_core/          <-- [Tự thêm] Folder bộ lõi Miniconda (Tự tìm trong máy và bỏ vào, sau đó đổi tên folder đấy thành "miniconda_core")
│
└── README.md
```

======================================================================

**🛠️ 2. HƯỚNG DẪN THIẾT LẬP VÀ KHỞI CHẠY (Chỉ làm lần đầu)**

Sau khi tải folder DuBaoBitcoin_vX.X từ GitHub về máy thì làm theo đúng 3 bước sau:

Bước 1: Chuẩn bị bộ lõi `miniconda_core`

1. Truy cập vào đường dẫn nơi bạn đã cài đặt Miniconda trên máy của bạn (Ví dụ: C:\ProgramData\Miniconda3 hoặc G:\Application\Miniconda3).
2. Copy nguyên folder `miniconda3` đó.
3. Ra ngoài thư mục cha `DuBaoBitcoin` (nằm song song với folder code của dự án), Paste folder đó vào và đổi tên chính xác thành: `miniconda_core`.

Bước 2: Đồng bộ thư viện và chạy ứng dụng

1. Vào bên trong folder code (Ví dụ: DuBaoBitcoin_v0.3).
2. Nhấp đúp chuột (Double click) vào file `ChayUngDung.bat`.
3. Hệ thống sẽ tự động kích hoạt bộ lõi, quét file `ThuVien.txt` để tự động cài đặt/cập nhật mọi thư viện còn thiếu (tensorflow, streamlit, yfinance,...) vào môi trường của bạn.

Bước 3: Trải nghiệm ứng dụng

- Sau khi đồng bộ xong (mất khoảng 1-2 phút ở lần đầu tiên), giao diện Web App của đồ án sẽ tự động mở ra trên trình duyệt mặc định của bạn.
- Từ các lần chạy sau, bạn chỉ cần bấm `ChayUngDung.bat` là ứng dụng sẽ lên ngay lập tức trong 3 giây.
