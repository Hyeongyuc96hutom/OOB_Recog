import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pandas import DataFrame as df

from itertools import groupby

import argparse
import json
import os


parser = argparse.ArgumentParser()

parser.add_argument('--title_name', type=str, help='plot title, and save file name')

parser.add_argument('--sub_title_name', type=str, help='sub plot title, and save file name')

parser.add_argument('--GT_path', type=str, help='GT model_inference assets path')

parser.add_argument('--model_name', type=str, nargs='+',
					choices=['resnet18', 'resnet34', 'resnet50', 'wide_resnet50_2', 'resnext50_32x4d', 'mobilenet_v2', 'mobilenet_v3_small', 'squeezenet1_0'], help='trained backborn model, it will be yticks name')

parser.add_argument('--model_infernce_path', type=str, nargs='+', help='model_inference_assets path. this order should be pair with --model_name. if not, results is not unpair.')

parser.add_argument('--results_save_dir', type=str, help='inference results save path')

parser.add_argument('--filter', type=str, nargs='?', choices=['mean', 'median'], help='only predict results will be apply')

parser.add_argument('--kernel_size', type=int, default=1, choices=[1,3,5,7,9,11,19], help='filter kernel size')

args, _ = parser.parse_known_args()

def encode_list(s_list): # run-length encoding from list
    return [[len(list(group)), key] for key, group in groupby(s_list)] # [[length, value], [length, value]...]


def medfilter (x, k):
	"""Apply a length-k median filter to a 1D array x.
	Boundaries are extended by repeating endpoints.
	"""
	assert k % 2 == 1, "Median filter length must be odd."
	assert x.ndim == 1, "Input must be one-dimensional."

	k2 = (k - 1) // 2
	y = np.zeros ((len (x), k), dtype=x.dtype)

	print('==> prepare')
	print(y)

	y[:,k2] = x
	
	print('\n==> arrange')
	print(y)
	for i in range (k2):
		j = k2 - i
		y[j:,i] = x[:-j]
		y[:j,i] = x[0]
		y[:-j,-(i+1)] = x[j:]
		y[-j:,-(i+1)] = x[-1]

	print('\n==> margin padding')
	print(y)

	return np.median (y, axis=1)


def meanfilter (x, k):
	"""Apply a length-k mean filter to a 1D array x.
	Boundaries are extended by repeating endpoints.
	"""
	assert k % 2 == 1, "Mean filter length must be odd."
	assert x.ndim == 1, "Input must be one-dimensional."

	k2 = (k - 1) // 2
	y = np.zeros ((len (x), k), dtype=x.dtype)
	y[:,k2] = x
	for i in range (k2):
		j = k2 - i
		y[j:,i] = x[:-j]
		y[:j,i] = x[0]
		y[:-j,-(i+1)] = x[j:]
		y[-j:,-(i+1)] = x[-1]
	return np.mean (y, axis=1)

def apply_filter(assets, filter_type:str, kernel_size) : # input = numpy, kernel should be odd

	print('\n\n\t\t ===== APPLYING FILTER | type : {} | kernel_size = {} =====\n\n'.format(filter_type, kernel_size))

	results = -1 # reutrn
	
	if filter_type == 'median' :
		results=medfilter(assets, kernel_size) # 1D numpy
		results=results.astype(assets.dtype) # convert to original dtype

		print('\t\t==> original \t')
		print(assets)
		print('\t\t==> results \t')
		print(results)

	elif filter_type == 'mean' :
		pass

	return results # numpy


# for text on bar
def present_text(ax, bar, text):
	for rect in bar:
		posx = rect.get_width()
		posy = rect.get_y() - rect.get_height()*0.3
		print(posx, posy)
		ax.text(posx, posy, text, rotation=0, ha='left', va='bottom')

# calc OOB_Metric
# input|DataFrame = 'GT' 'model A' model B' ..
# calc FN, FP, TP, TN
# out|{} = FN, FP, TP, TN frame
def return_metric_frame(result_df, GT_col_name, predict_col_name) :
    IB_CLASS, OOB_CLASS = 0,1

    print(result_df)
    
    # FN    
    FN_df = result_df[(result_df[GT_col_name]==OOB_CLASS) & (result_df[predict_col_name]==IB_CLASS)]
    
    # FP
    FP_df = result_df[(result_df[GT_col_name]==IB_CLASS) & (result_df[predict_col_name]==OOB_CLASS)]

    # TN
    TN_df = result_df[(result_df[GT_col_name]==IB_CLASS) & (result_df[predict_col_name]==IB_CLASS)]
    
    # TP
    TP_df = result_df[(result_df[GT_col_name]==OOB_CLASS) & (result_df[predict_col_name]==OOB_CLASS)]

    return {
        'FN_df' : FN_df,
        'FP_df' : FP_df,
        'TN_df' : TN_df,
        'TP_df' : TP_df,
    }

# calc OOB Evaluation Metric
def calc_OOB_Evaluation_metric(FN_cnt, FP_cnt, TN_cnt, TP_cnt) :
	base_denominator = FP_cnt + TP_cnt + FN_cnt	
	# init
	EVAL_metric = {
		'OOB_metric' : -1,
		'correspondence' : -1,
		'UN_correspondence' : -1,
		'OVER_estimation' : -1,
		'UNDER_estimtation' : -1,
		'FN' : FN_cnt,
		'FP' : FP_cnt,
		'TN' : TN_cnt,
		'TP' : TP_cnt,
		'TOTAL' : FN_cnt + FP_cnt + TN_cnt + TP_cnt
	}

	if base_denominator > 0 : # zero devision except check, FN == full
		EVAL_metric['OOB_metric'] = (TP_cnt - FP_cnt) / base_denominator
		EVAL_metric['correspondence'] = TP_cnt /  base_denominator
		EVAL_metric['UN_correspondence'] = (FP_cnt + FN_cnt) /  base_denominator
		EVAL_metric['OVER_estimation'] = FP_cnt / base_denominator
		EVAL_metric['UNDER_estimtation'] = FN_cnt / base_denominator
		
	return EVAL_metric



def main():

	print(json.dumps(args.__dict__, indent=2))


	#### 1. bar plot으로 나타낼 데이터 입력
	IB, OOB = (0,1) # class index
	
	### for plt variable, it should be pair sink
	label_names = ['IB', 'OOB']
	colors = ['cadetblue', 'orange']
	height = 0.5 # bar chart thic

	## Data prepare
	print(args.GT_path)
	print('------')
	GT_df = pd.read_csv(args.GT_path)
	frame_label = list(GT_df['frame']) # sync xticks label from GT
	time_label = list(GT_df['time']) # sync xticks label from GT

	yticks = ['GT'] # y축 names # 순서중요
	yticks += args.model_name

	predict_data = {'GT': GT_df['truth']}
	
	# pairwise read
	for y_name, inf_path in zip(args.model_name, args.model_infernce_path) :
		p_data = pd.read_csv(inf_path)['predict']

		# filter processing		
		if args.filter is not None :
			p_data = apply_filter(p_data.to_numpy(), args.filter, args.kernel_size) # 1D numpy, 'filter', kernel_size
			p_data = pd.Series(p_data)

		
		predict_data[y_name] = p_data


	print(predict_data)
	
	'''
	data = {'GT': [1, 1, 1, 0, 0, 1, 1, 1], # 0번 ~ 2번 frame , 5번 ~ 7번 frame
	        'Model A': [0, 0, 1, 1, 0, 0, 1, 1], # 2번 ~ 3번 frame
			'Model B': [1, 0, 1, 1, 1, 0, 1, 0] # 0번 ~ 0번 frame, 2번 ~ 4번 frame, 6번 ~ 6번 frame
			}
	'''

	## Data preprocessing

	# run-length encoding
	encode_data = {}
	for y_name in yticks :
		encode_data[y_name] = df(data=encode_list(predict_data[y_name]), columns=[y_name, 'class']) # [length, value]

	print(encode_data)
	
	# arrange data
	runlength_df = df(range(0,0)) # empty df
	for y_name in yticks :
		runlength_df = runlength_df.append(encode_data[y_name])

	# Nan -> 0, convert to int
	runlength_df = runlength_df.fillna(0).astype(int)
	print(runlength_df)	

	'''
	runlength_df = df([[3,0,0,1],
				[2,0,0,0],
				[3,0,0,1],
				[0,2,0,0],
				[0,2,0,1],
				[0,2,0,0],
				[0,2,0,1],
				[0,0,1,1],
				[0,0,1,0],
				[0,0,3,1],
				[0,0,1,0],
				[0,0,1,1],
				[0,0,1,0]], columns= yticks + ['class'])
	'''

	# split data, class // both should be same length
	runlength_class = runlength_df['class'] # class info
	runlength_model = runlength_df[yticks] # run length info of model prediction

	print(runlength_class)
	print(runlength_model)

	#### 2. matplotlib의 figure 및 axis 설정
	fig, ax = plt.subplots(1,1,figsize=(12,8)) # 1x1 figure matrix 생성, 가로(7인치)x세로(5인치) 크기지정
	
	##### initalize label for legned, this code should be write before writing barchart #####
	init_bar = ax.barh(range(len(yticks)), np.zeros(len(yticks)), label=label_names[IB], height=height, color=colors[IB]) # dummy data
	init_bar = ax.barh(range(len(yticks)), np.zeros(len(yticks)), label=label_names[OOB], height=height, color=colors[OOB]) # dummy data
	##### #### #### #### ##### #### #### #### 


	# data processing for barchart
	data = np.array(runlength_model.to_numpy()) # width
	data_cum = data.cumsum(axis=0) # for calc start index

	print(data)
	print(data_cum)

	#### 3. bar 그리기
	for i, frame_class in enumerate(runlength_class) :
		print(data[i,:])
		print(frame_class)

		widths = data[i,:]
		starts= data_cum[i,:] - widths
		
		bar = ax.barh(range(len(yticks)), widths, left=starts, height=height, color=colors[frame_class]) # don't input label

	
	#### 3_1. Evaluation Metric calc 및 barchart oob metric 삽입
	Total_Evaluation_df = df(index=range(0, 0), columns=['Model', 'kernel_size', 'OOB_metric', 'correspondence', 'UN_correspondence', 'OVER_estimation', 'UNDER_estimtation', 'FN', 'FP', 'TN', 'TP', 'TOTAL'])

	for i, model in enumerate(yticks) :
		print(i, model)
		# calc Evaluation Metric
		metric_frame_df = return_metric_frame(df(predict_data), 'GT', model)
		
		Evaluation_metric = calc_OOB_Evaluation_metric(len(metric_frame_df['FN_df']), len(metric_frame_df['FP_df']), len(metric_frame_df['TN_df']), len(metric_frame_df['TP_df']))
		Evaluation_df = df(Evaluation_metric, index=[0])

		Evaluation_df.insert(0, 'kernel_size', args.kernel_size)
		Evaluation_df.insert(0, 'Model', model)

		print(Evaluation_df)

		Total_Evaluation_df = pd.concat([Total_Evaluation_df, Evaluation_df], ignore_index=True)

		text_bar = ax.barh(i, 0, height=height) # dummy data
		present_text(ax, text_bar, ' OOB_METRIC : {:.3f} | OVER_ESTIMATION : {:.3f} | UNDER_ESTIMATION : {:.3f} \n FN : {} | FP : {} | TN : {} | TP : {} | TOTAL : {}'.format(Evaluation_metric['OOB_metric'], Evaluation_metric['OVER_estimation'], Evaluation_metric['UNDER_estimtation'], Evaluation_metric['FN'], Evaluation_metric['FP'], Evaluation_metric['TN'], Evaluation_metric['TP'], Evaluation_metric['TOTAL']))
	
	print(Total_Evaluation_df)

	# Evaluation Metric save
	Total_Evaluation_df.to_csv(os.path.join(args.results_save_dir, '{}-{}-Evaluation.csv'.format(args.title_name, args.sub_title_name)), mode='w') # mode='w', 'a'
 
		
	
	#### 4. title 설정
	fig.suptitle(args.title_name, fontsize=18)
	ax.set_title(args.sub_title_name)

	#### 5. 

	#### 6. x축 세부설정
	step_size = 3000 # xtick step_size
	ax.set_xticks(range(0, len(frame_label), step_size)) # 3000
	ax.set_xticklabels(['{}\n{}'.format(time, frame) for time, frame in zip(frame_label[::step_size], time_label[::step_size])]) # xtick change
	ax.xaxis.set_tick_params(labelsize=7)
	ax.set_xlabel('Frame / Time (h:m:s:fps)', fontsize=12)
	
	#### 7. y축 세부설정
	ax.set_yticks(range(len(yticks)))
	ax.set_yticklabels(yticks, fontsize=10)	
	ax.set_ylabel('Model', fontsize=12)
	
	#### 8. 범례 나타내기
	box = ax.get_position() # 범례를 그래프상자 밖에 그리기위해 상자크기를 조절
	ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
	ax.legend(label_names, loc='center left', bbox_to_anchor=(1,0.5), shadow=True, ncol=1)
	
	#### 9. 보조선(눈금선) 나타내기
	ax.set_axisbelow(True)
	ax.xaxis.grid(True, color='gray', linestyle='dashed', linewidth=0.5)
	
	#### 10. 그래프 저장하고 출력하기
	plt.savefig(os.path.join(args.results_save_dir, '{}-{}.png'.format(args.title_name, args.sub_title_name)), format='png', dpi=500)
	plt.show()


if __name__=='__main__':
	main()