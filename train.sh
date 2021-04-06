for lr in 1e-3
do
    python train_camIO.py \
    --project_name="robot_oob_0405" \
    --max_epoch=50 \
    --log_path="/OOB_RECOG/logs" \
    --batch_size=32 \
    --init_lr=${lr}
done