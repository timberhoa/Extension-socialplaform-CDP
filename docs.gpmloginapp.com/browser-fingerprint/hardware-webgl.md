# Hardware: WebGL

WebGL là một API Javascript giúp trình duyệt render các khối 3D (như một khối tam giác 3D, hình hộp…), mỗi loại card khi render cũng sẽ hơi khác nhau một chút, thuật toán khử răng cưa, làm mịn ảnh cũng khác nhau nên đây cũng là một trong những thông số giúp xác định sự khác nhau giữa các loại card màn hình. Việc render 3D phức tạp hơn render 2D rất nhiều và có khá nhiều tùy chỉnh nâng cao nhất là đối với các loại card rời hiện nay, nên việc thêm noise đúng kỹ thuật trong quá trình render là khá tốt đối với nhiều website.

**Đặc điểm của kĩ thuật noise**

1 . Kĩ thuật noise không thể biến hình ảnh sau render của card đồ họa A giống hệt với hình ảnh sau render của card đồ họa B, giống như việc phẫu thuật thẩm mỹ, không thể phẫu thuật người A thành người B được (tất cả chi tiết từng chân tơ kẽ tóc), mà chỉ làm người A lúc sau khác với người A lúc trước.&#x20;

2 . Kĩ thuật này giúp tạo nên sự đa dạng và tính duy nhất rất lớn cho fingerprint.

3 . Kĩ thuật noise có thể bị phát hiện bởi các hệ thống lớn có thu thập big data để kiểm tra

Nếu chỉ xét riêng một thông số canvas, có hàng chục triệu máy tính khác nhau trên khắp thế giới giống nhau (sử dụng cùng loại card đồ họa, cài cùng hệ điều hành và trình duyệt), nhưng kĩ thuật noise sẽ khiến bạn có tính duy nhất rất cao.

Ví dụ đơn giản:&#x20;

Facebook có hàng tỉ người truy cập mỗi ngày, họ thu thập các mã hash canvas lưu lại, khi bạn truy cập nếu bạn giống rất nhiều người khác là điều bình thường, nhưng bạn là duy nhất mới là điều đáng nghi và gần như không thể xảy ra (bạn không thể sử dụng một loại card đồ họa, cài hệ điều hành và trình duyệt mà không ai trong số hàng tỉ người đó có)
