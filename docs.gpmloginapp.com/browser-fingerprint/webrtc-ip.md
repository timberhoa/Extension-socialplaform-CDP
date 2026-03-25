# WebRTC IP

WebRTC là một công nghệ giúp hai thiết bị có thể kết nối trực tiếp với nhau mà không quan tâm tới các kết nối trung gian, nó được sử dụng trong các ứng dụng cần kết nối nhanh như video call.

*Trước khi có WebRTC, 2 người dùng facebook muốn video call cho nhau thì đều phải gửi / truyền các gói tin qua server facebook (thường bên US, từ VN->US->VN rất mất thời gian), điều này vừa làm cho server facebook chịu tải cao, vừa làm trải nghiệm khách hàng không tốt vì thời gian kết nối chậm dẫn tới giật, lag.*

*Khi có WebTRC, 2 thiết bị của người dùng có thể khởi tạo kết nối trực tiếp cho nhau (thông thường sử dụng UDP), việc này giúp tốc độ kết nối tốt và giảm tải rất nhiều cho server.*\
\
**Chính vì có kết nối trực tiếp, bỏ qua các kết nối trung gian, WebRTC cũng được ứng dụng trong vấn đề bảo mật để xác định IP thật của người dùng.**\
\
Website sẽ yêu cầu máy tính kết nối WebRTC, sau khi kết nối thành công, máy tính và website sẽ có kết nối trực tiếp và hoàn toàn bỏ qua các proxy trung gian nếu có, từ đây website có thể lấy được IP thật của thiết bị thông qua 2 cách:\
\
\+ Đọc trong gói tin UDP (thường được sử dụng)

\+ Yêu cầu Stun server lấy và trả về kết quả (Ebay sử dụng cách này)\
\
Việc của antidetect là ghi đè IP thật trong gói tin UDP cũng như xử lý với stun server.\
\
Tìm hiểu thêm tại youtube của giaiphapmmo.vn
