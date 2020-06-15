# SMS

A connector for text messages, using the [Twilio](https://twil.io) API.

## Requirements

This requires a Twilio API Key, which is availible from [here](https://twil.io). Follow the below steps to set it up:

1. Create a free or paid Twilio account. If you sign up through [this link](https://www.twilio.com/try-twilio?promo=YbalWV)  you will get a $10 credit when you upgrade.

2. Install the Twilio CLI <div><details> <summary>Mac</summary> <code>brew tap twilio/brew && brew install twilio</code><br/><h4>Or Install via npm</h4><code>npm install twilio-cli -g</code></details><details><summary>Windows</summary><code>npm install twilio-cli -g
</code></details><details><summary>Linux</summary>Please see the Twilio Docs</details></div>

3. Run `twilio login`. Use the account information from you [Twilio console](https://www.twilio.com/console).Click the eye icon as shown below to reveal your account secret. <br/> ![account secret](https://twilio-cms-prod.s3.amazonaws.com/images/account_sid_auth_token.width-800.png)

4. Run `twilio phone-numbers:buy:local --country-code US --sms-enabled` if you need to buy a phone number.

## Configuration

```yaml
connectors:
  sms:
    name: "bot-name"  #optional
    account_sid: "ACxxxxxxxxxxxxxx" # required
    auth_token: "token"
    phone_number: "+1555555555"
    is_trial: true
    approved_trial_numbers: # required if is_trial is true
        - "+15555555555"
```

`name`: optional, string, bot name

`account_sid`: required, string, your Twilio Account SID <br/>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Go to [your Twilio Console](https://twilio.com/console) to find your SID. See the below image.

`auth_token`: required, string, your Twilio Account Auth Token <br/>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Go to [your Twilio Console](https://twilio.com/console) and click the eye icon to reveal your token.

![account secret](https://twilio-cms-prod.s3.amazonaws.com/images/account_sid_auth_token.width-800.png)

`phone_number`: required, string, the phone number from you Twilio account. If you followed the setup, this is the number you registered. <br/>

`is_trial`: required, boolean <br/>

`approved_trial_numbers`: required if `is_trial ` is set to "true", list
