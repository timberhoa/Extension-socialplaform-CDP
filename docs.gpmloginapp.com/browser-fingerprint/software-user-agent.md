# Software:User agent

User-agent là một chuỗi kí tự đại diện cho 4 thông số (Hệ điều hành, phiên bản hệ điều hành, Loại trình duyệt, phiên bản trình duyệt). User agent được gắn vào mỗi request gửi đi từ trình duyệt giúp website ban đầu nhận biết được bạn đang sử dụng hệ điều hành, loại trình duyệt nào để hiển thị giao diện phù hợp (Ví dụ bạn sử dụng mobile, website hiển thị giao diện cho mobile, sử dụng PC website sử dụng giao diện cho PC…), hoặc phân chia chức năng phù hợp.

Ví dụ xét user agent sau:\
\
`Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36`<br>

Từ đây website có thể nhận diện bạn đang sử dụng trình Windows NT 10.0 (là core của windows 10 và windows 11), 64bit, sử dụng Chrome phiên bản 118.0.0.0

User agent hoàn toàn không có tính duy nhất, ngược lại là quá đại trà, vì xét ví dụ trên: toàn bộ máy tính cài đặt Windows 10, 11 và sử dụng Chrome đều có useragent giống hệt nhau.\
Tuy nhiên, việc thay đổi User-agent cũng giúp bypass một số website, nhưng ngược lại cũng có thể giúp nhiều website nghi ngờ bạn là một người sử dụng “không thật” khi so sánh useragent với các thông số phần mềm (Hệ điều hành, Phiên bản trình duyệt) được gửi lên từ Javascript.\
Theo quan điểm cá nhân của mình, nếu không có TUT,TIP gì đó thì không nên thay đổi thông số này.

**Tại sao website có thể nhận diện được bạn đang sử dụng hệ điều hành nào và trình duyệt nào?**\
Mỗi hệ điều hành hay trình duyệt, hoặc chi tiết hơn là mỗi phiên bản trên cùng một trình duyệt đều có một số component đặc biệt và nó cũng cung cấp javascript để gọi ra các thông số này. Từ đây website có thể gọi và đoán xem bạn đang sử dụng hệ điều hành nào, trình duyệt và phiên bản trình duyệt nào (dù không chính xác tuyệt đối nhưng nếu bạn fake sai cũng có thể bị phát hiện).
