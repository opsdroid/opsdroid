# How are you?

opsdroid가 "how are you"라는 텍스트에 응답하도록 만드는 기본 스킬을 만들 것입니다. 자신만의 스킬을 만들기 위한 비디오 튜토리얼도 여기에서 이용할 수 있습니다. [here](https://www.youtube.com/watch?v=gk7JN4e5l_4&index=3&list=PLViQCHlMbEq5nZL6VNrUxu--Of1uCpflq).

*도움이 필요하거나 확실하지 않은 사항이 있으면 매트릭스 채널에 가입하여 문의해 보십시오! 우리는 당신을 도울 수 있다면 매우 기쁩니다.* [matrix channel](https://app.element.io/#/room/#opsdroid-general:matrix.org)

## The Skill folder
opsdroid 스킬은 skill-<skillname> 라는 이름의 폴더 안에 있습니다. 이 폴더 안에 다음 파일이 있어야 합니다.

- `LICENSE`
- `README.md`
- `__init__.py`

__init_.py 파일에 파이썬 기능을 모두 작성하겠지만, 스킬 폴더 안에 다른 유용한 파일도 포함할 수 있습니다.

## Building the Skill
이제 'How are you' 스킬을 쓸 준비가 되었습니다. 우리는 함수를 쓰기 위해 opsdroid regex matcher를 사용할 것입니다. __init_.py 내부에서 가장 먼저 해야 할 일은 opsdroid에서 상속할 스킬 클래스를 가져오는 것입니다.

#### Importing the skill class

```python
from opsdroid.skill import Skill
```

#### Importing Regex Matcher

또한 기술 class의 방법을 사용자 언어의 구나 문장에 연결하는 데 사용할 수 있는 매처도 필요합니다.

```python
from opsdroid.matchers import match_regex
```
opsdroid에서 사용할 수 있는 모든 매처는 opsdroid.matchers에서 가져올 수 있습니다.

#### Decorators
매처는 데코레이터로 사용됩니다. 데코레이터는 opsdroid가 그 기능을 이해할 수 있도록 합니다. 그래서 우리는 이 데코레이터를 사용해야 합니다. 그리고 우리는 opsdroid가 반응하는 regex를 사용해야 합니다.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

class MySkill(Skill):

    @match_regex('how are you?')
```

[regex matcher](../skills/matchers/regex)는 사용자가 보낸 모든 메시지에서 그것을 검색합니다. 만약 사용자가 how are you?를 입력한다면 opsdroid는 match_regex 데코레이터 아래에 함수를 실행합니다

_Note: 물음표가 없기 때문에 opsdroid가 텍스트와 함께 실행되지 않습니다._

#### Functions
opsdroid의 기술은 파이썬 class 메소드입니다. 앞에서 보았듯이, 데코레이터와 메소드가 함께 있으면 여러분이 상상할 수 있는 거의 모든 것을 할 수 있습니다.
    
우리의 함수를 적어봅시다. 이로써 사용자가 how are you?라는 단어를 쓸 때 opsdroid가 무엇을 실행할지 알게 됩니다.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

class MySkill(Skill):

    @match_regex('how are you?')
    async def how_are_you(self, message):
        pass
```

opsdroid는 비동기 방식으로 제작됩니다. 즉, opsdroid가 반응할 모든 함수는 비동기 함수여야 합니다.

_Note: 모든 기능에는 self, message라는 두 가지 매개 변수가 사용됩니다._

#### Opsdroid Answer
이제 우리의 opsdroid는 사용자가 말한 것에 맞추어 기술을 실행할 수 있습니다. 하지만 아직 아무 일도 일어나지 않을 것입니다. 텍스트에 대한 opsdroid 답변을 만들어 봅시다. 자신만의 메시지로 말이죠.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

class MySkill(Skill):

    @match_regex('how are you?')
    async def how_are_you(self, message):
        await message.respond('Good thanks! My load average is 0.2, 0.1, 0.1.')
```

우리의 기술은 완성되었고 opsdroid는 opsdroid 메인 페이지에서와 같이 반응할 수 있을 것입니다. 마지막으로 opsdroid 구성 파일에 스킬을 추가해 봅시다.


#### Adding the Skill To Configuration
단순하게 하기 위해 다음과 같이 가정하겠습니다.

-구성 파일은 ~/.opsdroid/configuration.yaml 에 있습니다.
-당신의 스킬은 ~/documents/skill-howareyou 에 있습니다.

configuration.yaml 파일을 열고 스킬 섹션에서 스킬의 이름과 경로를 추가합니다.:

```yaml
skills:
  how-are-you:
    path: /Users/username/documents/skill-howareyou
```

탭 대신 공백을 사용하는 것이 매우 중요합니다. opsdroid를 실행할 때 문제가 있으면 이 두 가지를 모두 확인하십시오. 공간의 문제일 수 있습니다.

더 많은 스킬의 예시는 opsdroid 체크 아웃 예제 섹션을 통해 빌드할 수 있습니다.
 [examples section](../examples/index).
