# Facebook Messenger

페이스북을 위한 connector [Facebook Messenger](https://developers.facebook.com/docs/messenger-platform/).

## Requirements

이 connector는 당신의 페이스북 페이지 access token이 필요하다.

Access token을 얻기 위한 스탭은 다음과 같다.
-	당신의 bot의 페이스북 페이지를 개설한다.
-	https://developers.facebook.com 에 접속한다.
-	새 app을 만든다
-	앱이 만들어지면 앱 설정에 들어가서 PRODUCTS에 들어가서 Add Product  Select Messenger  Set up the messenger product 선택한다.
-	Facebook APIs를 이용하기 위해서 당신 페이지의 page-access-token을 만들어라.
-	http(s)://your-bot-url.com:port/connector/facebook로 webhook pointing을 만든다. 
-	무작위로 verify-token을 만들고 webhook에 추가한다.

## Configuration

```yaml
connectors:
  facebook:
    # required
    verify-token: aabbccddee
    page-access-token: aabbccddee112233445566
    # optional
    bot-name: "mybot" # default "opsdroid"
```
