# Out of Body Recognition Project

## 프로젝트 개요
VI Hub를 통해 녹화되는 영상에 대해 환자의 몸속 영상인지, 아닌지를 구분하기 위한 프로젝트

해당 프로젝트를 위해 크게 3가지 Step으로 진행

### Task
1. Inbody, Out of Body [Binary Classification] ==> OOB Task
    - 몸속 안 영상인지, 밖 영상인지 구분하는 Task
    - 해당 Model의 목표치는 FP = 0 에 수렴하도록 학습 (즉, Out body를 Positive라 할때, 모델이 Out Body라고 예측했지만 실제로는 Inbody인 경우) 
2. NIR, RGB (Binary Classification) ==> NIR Task
    - NIR (혈관 조영모드) , RGB 인지 구분하는 Task

3. 서로다른 Device로 획득한 영상 (Robot, Lapa) 에 대한 개별모델이 아닌, 동일한 모델사용시 최적의 성능이 보장되는지에 대한 실험
    - 개뱔 Dataset에 Fitting된 모델학습 후 다른 Device영상 Inference 하여 성능비교

### Dataset
- Robot 40개 [35 / 5] [train / validation]
- Lapa 40개 [35 / 5] [train / validation]
- Robot + Lapa [70 / 10] [train / validation]
    
    [Validation Set Info](https://www.nature.com/articles/s41598-020-79173-6.epdf?sharing_token=57pWgB367cI5coHzkZUDR9RgN0jAjWel9jnR3ZoTv0MCV8TIltOg1hyPQGUx3RpjykRBW7tAmqhJCZlzxL0s2NSSWKMZpEM3UFO4sTQKqx7neUFX9oBn_x6p5BDC04YK7SP82L6tnjqWQ_lomdL75_4pkUeZjpjF_9ZzkYi6Fhg%3D)

### Referecne paper
[Accurate Detection of Out of Body Segments in Surgical
Video using Semi-Supervised Learning](http://proceedings.mlr.press/v121/zohar20a/zohar20a.pdf)

--- 
## Development Log
- 2021/03/19 | @bgpark
    1. First Init with Baseline Code
    2. create Init docker

- 2021/03/29 | @hyeongyu
    1. Modify Baseline Code
    2. Create new video Inference code for robot => new_test_video.py

- 2021/03/31 | @hyeongyu
    1. Bugfix
        - gen_dataset.py
            - CAMIO_Dataset(Dataset) : change way to get dataset
        - new_video_test.py
            - change input img tensor format -> .cuda()
    
    2. Modify train_CamIO.py
        - add code for dataset log check
---

## 사용법
```bash
# nvidia-docker repository 등록
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# package list update & install
sudo apt-get update
sudo apt-get install -y nvidia-docker2

# 간단 test
docker run --runtime=nvidia --rm nvidia/cuda:10.0-base nvidia-smi
```

docker build & run

```jsx
# Dockerfile이 있는 곳에서
# docker image building
sudo docker build -t <원하는 도커 이미지 이름>:<버전 정보 원하면> .
# ex) sudo docker build -t pyl:1.0 .

# docker container running
sudo docker -it -d -v <공유할 폴더 위치>:<컨테이너 내부 공유폴더 위치> --gpus all --name <원하는 컨테이너 이름> <실행하길 원하는 도커 이미지>
# ex) sudo docker -it -d /nas/bgpark/CAM_IO:/data/CAM_IO --gpus all --name pyl-test pyl:1.0

# docker 내부로 진입
# bash shell 실행
sudo docker exec -it pyl-test /bin/bash
```
--- 
## Easy Command
- docker container 생성 (gpu all, volumn 연동, 포트포워딩, ipc 설정)
```shell
docker run -it --name cam_io_hyeongyu -v /home/hyeongyuc/code/CAM_IO:/CAM_IO -v /nas/bgpark:/data -p 6006:6006  —-gpus all --ipc=host cam_io:1.0
```

- Tensorboard 사용을 위한 ssh 포트포워딩
```shell
ssh -L 6006:localhost:6006 hyeongyuc@192.168.1.15
```

- Tensorboard 사용
```shell
tensorboard --logdir=/CAM_IO/logs/OOB_robot_test/DPP_Test/version_0 --bind_all
```

- GPU 확인
```shell
watch -d -n 0.5 nvidia-smi
