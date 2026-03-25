# TCP/IP Fingerprint

Đây là một phương án khá tốt để phát hiện người dùng có đang sử dụng Proxy hay không, đại loại nó dựa trên sự đặc trưng của gói tin nhận về để xác định nó được tạo ra từ hệ điều hành nào. Ví dụ bạn sử dụng Windows nhưng sử dụng Proxy được tạo ra bởi server linux (đa số máy chủ proxy đều sử dụng linux) thì bạn được xác định là đang sử dụng Proxy. \
\
Việc sử dụng Proxy là không bị ngăn cấm nhưng cũng là một yếu tố đánh giá bạn là một người dùng không tốt. Phía client sẽ không thể xử lý được việc này mà máy chủ Proxy sẽ phải xử lý lại gói tin gửi đi sao cho giống với hệ điều hành của client. Vì thế chọn nhà cung cấp Proxy cũng rất quan trọng.
