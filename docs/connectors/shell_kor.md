# Shell

Command line을 통해 opsdroid로 메시지 송신하는 connector [opsdroid](https://github.com/opsdroid/opsdroid).

이 connector는 unix환경에서만 작동을 한다. 윈도우에서는 작동이 되지 않는다. 윈도우에서 활용하려면 Opsdroid 컴퓨터 어플을 다운로드 해야한다.
[Opsdroid Desktop App](https://github.com/opsdroid/opsdroid-desktop).

## Requirements

Shell connector는 사용자의 정보를 필요로 한다.

## Configuration

```yaml
connectors:
  shell:
    # optional
    bot-name: "mybot" # default "opsdroid"
```

## Disable Logging

console 로그인을 비활성화하는 것을 추천한다. Configuration.yaml을 이용해서 connector를 추가하면 된다. 다음 줄을 configuration 파일에 추가하면 된다.


```yaml
logging:
  console: false
```
