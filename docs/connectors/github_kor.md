# GitHub

Opsdroid의 connector는  [opsdroid](https://github.com/opsdroid/opsdroid) Github의 [GitHub](https://github.com)issues와 pull request를 지원한다. 이 Connector는 너에게 CI check에서 오는 이벤트를 제공한다.
## Requirements

Github connector을 사용하기 위해서 bot을 위해 사용자마다 개인별 api token을 생성해야한다. 당신의 메인 계정을 사용하기 보다는 별도의 계정을 사용하는 것을 권장한다. 당신은 opsdroid에 이벤트를 송신하기 위해서 별도의 webhook을 구성해야 한다. 이 행위를 위해서 인터넷 tunnel에 opsdroid를 노출시켜야 한다.
### Creating your application

There are 2 ways to connect opsdroid to Github. You can create a Github App and point it at opsdroid for event handling. This app can be installed by multiple organizations and would only be configured once. The other way is to use a Webhook within Github and point that to opsdroid for event handling. Each webhook needs to be individually configured.

#### Github Apps method

Opsdroid와 Github의 연결에는 두가지 방법이 있다. 첫번째로는 당신이 Github앱을 만들고 이벤트 핸들링을 위해 이를 opsdroid로 포인팅하는 방법이다. Github앱은 다양한 구축환경에서도 설치가 가능하고 구성하는 것도 일회성으로 충분하다. 두번째 방법으로는 Webhook을 이용해서 이벤트 핸들링을 위해 opsrdoid와 Github를 연결하는 것이다. 각 webhook은 개별적으로 구성되어야 한다.
Github Apps method
-	Github 앱을 설치한다.
-	Webhook URL을 구성하고 이를 opsdroid url로 포인팅한다
-	사용자로부터 허가를 받는다. 지원하는 값들은 다음과 같다.
	“Checks”
	“Contents”
	“Issues”
	“Pull requests”
-	당신의 선택에 의해서 Github에서 당신의 opsdroid로 송신하는 이벤트들을 결정할 수 있다. 지원하는 값들은 다음과 같다.
	“Check runs”
	“Issues”
	“Issue comment”
	“Pull request”
	“Pull request review”
	“Pull request review comment”
	“Push”
-	“Create GitHub App”을 클릭하고 개인 키를 발급 받는다.

#### Webhook method

-	GitHub 사용자를 만들고 로그인한다.
	만일 bot이 GitHub로 너무 많은 메시지를 보낸다면 금지 당할 수 있다.
-	개인 api token을 생성한다.
-	Bot이 실행했으면 하는 comment를 repo로 연결한다.
-	설정 화면으로 이동한다.
-	Webhook 창에서 “Add webhook”을 누른다.
-	파일 경로가 application/x-www-form-urlencoded 인지 확인한다.
-	당신의 opsdroid url로 포인팅 된 webhook을 생성한다.
-	bot으로 보낼 event를 선택한다. 당신이 직접 개별적 event를 실행 할 수 있다. 지원하는 값은 다음과 같다.
	“Check runs”
	“Issues”
	“Issue comment”
	“Pull request”
	“Pull request review”
	“Pull request review comment”
	“Push”

## Configuration

#### Github app

```yaml
connectors:
  github:
    # required
    app_id: 123456
    private_key_file: <path/to/private_key.pem>
    secret: <webhook secret>
```

#### Webhook method

```yaml
connectors:
  github:
    # required
    token: aaabbbcccdddeee111222333444
    secret: <webhook secret>
```

## Reference

```eval_rst
.. autoclass:: opsdroid.connector.github.ConnectorGitHub
  :members:
```

## Events Reference

```eval_rst
.. autoclass:: opsdroid.connector.github.events.IssueCreated
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.IssueClosed
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.IssueCommented
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.Push
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.PROpened
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.PRReopened
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.PREdited
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.PRMerged
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.PRClosed
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.PRReviewSubmitted
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.PRReviewEdited
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.PRReviewDismissed
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.PRReviewCommentCreated
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.PRReviewCommentEdited
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.PRReviewCommentDeleted
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.Labeled
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.Unlabeled
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.CheckStarted
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.CheckCompleted
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.CheckPassed
  :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.github.events.CheckFailed
  :members:
```