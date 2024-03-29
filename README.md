
온도, 습도, 풍속, 외부 온도를 지정하여 온습도 센서의 기능을 확장할 수 있는 통합구성요소 입니다.


설치시 온도 습도는 필수이고 풍속은 옵션입니다. 풍속을 입력하게 되면 체감온도가 추가 됩니다.


---

## - 설치 방법

###

수동설치

- 소스코드를 다운로드 받은 후 HA 내부의 custom_components 경로에 extend_temperature 폴더를 넣어주고 재시작


- HACS
HACS 의 custom repository에 https://github.com/oukene/extend_temperature 주소를 integration 으로 추가 후 설치




설치 후 통합구성요소 추가하기에서 extend temperature 검색 한 후 추가를 진행하면 아래와 같이 입력하는 화면이 나옵니다.


![settings.jpg](https://raw.githubusercontent.com/oukene/extend_temperature/main/images/settings.jpg)
![settings2.jpg](https://raw.githubusercontent.com/oukene/extend_temperature/main/images/settings2.jpg)


기존에 추가되어있는 구성요소에서 사용하고자 하는 온도와 습도의 entity id 를 입력해줍니다.

체감온도를 사용하려면 풍속과 체감 온도 계산에 쓰일 온도의 구성요소를 같이 입력하면 됩니다. (풍속의 단위는 m/s)
mold indicator를 사용하려면 외부온도 구성요소를 입력하면 됩니다. (풍속의 단위는 m/s)

<br><br>
---
History
<br>
v1.0.0 - 2021.12.06 - 최초 작성<br>
v1.0.0 - 2021.12.07 - HA 재부팅시 버그 수정<br>
v1.1.0 - 2021-12-30 - mold indicator 추가, 체감온도 계산공식 수정, 소숫점 자릿수 옵션 추가<br>
v1.2.0 - 2022-01-26 - 센서에 사용되는 명칭 언어 선택추가, 추가 직후 바로 적용 안되던 부분 수정<br>
v1.3.0 - 2022-02-07 - ha의 버전업에 따른 수정과 온도, 습도 구성요소 변경시 오작동 되던 부분 수정 <br>
v1.4.0 - 2022-12-15 - 옵션 변경 후 다시 읽어오기 없이도 작동되도록 수정 <br>

---
<br><br><br>

https://github.com/dolezsa/thermal_comfort

위의 통합구성요소를 참고하여 작성되었습니다.
