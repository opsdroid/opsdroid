# Flip A Coin
동전 던지기를 수행하는 opsdroid 기술입니다.

## Setting Up
먼저 opsdroid 스킬 디렉터리를 만들어야 합니다. 파일 시스템의 어느 곳에나 위치할 수 있으므로 나중에 위치를 기억하기만 하면 됩니다. 이 예시에서는 ~/opsdroid/skills에 새 폴더를 만듭니다.

```shell
$ mkdir -p ~/opsdroid/skills/flip-coin
```

## The skill

그런 다음 이 폴더 안에 __init_py라는 파일을 만들고 다음 패키지를 가져와야 합니다.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

import random
```

둘째, 스킬에 대한 클래스를 만듭니다.

```python
class CoinSkill(Skill):
    @match_regex('flip a coin')
    async def flip_a_coin(self, message):
        if random.randint(0, 1):
            response = "Heads"
        else:
            response = "Tails"

        await message.respond("{}".format(response))

```

## Configuration

셋째, 'configuration.yaml' 파일을 엽니다. opsdroid config edit 명령을 사용하여 이 작업을 자동으로 수행할 수 있습니다.

그런 다음 스킬 섹션에 다음을 추가합니다.


```yaml
skills:
  flip-a-coin:
  path: ~/opsdroid/skills/flip-coin
```

이제 구성을 저장하고 opsdroid를 다시 로드합니다.

더 많은 스킬의 예시는 opsdroid 체크 아웃 예제 섹션을 통해 빌드할 수 있습니다.
[examples section](../examples/index).
