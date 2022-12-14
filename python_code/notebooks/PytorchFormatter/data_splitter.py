import pandas as pd

def split_df_for_TSF(df, PERIOD, PREDICTION, print_every = 500, log_file=None):
    """
    Split the dataframe df in train and test, accoding to the time division and with anomalies only in test.
    @df: the dataframe, must have a datetime field
    @PERIOD: is the dimension of the train (in hours)
    @PREDICTION: is the dimension of the test (in hours)
    @print_every: how many element to process before printing
    @log_file: where the log file should be stored. If none is provided, the warning are printed on screen.

    for each datetime starting from the minimum in the dataframe,
    split the dataframe in 
    train = df[current_time, current_time + PERIOD]
    and 
    test = df[current_time + PERIOD, current_time + PERIOD + PREDICTION]

    finally return the train and the test and the number of points to be predicted. 
    This is different from the old implementation because it remove the nans
    """    
    date_min = df['datetime'].min()
    date_max = df['datetime'].max()
    current_date = date_min
    i = 0
    data_train = []
    data_test = []
    print_status=True
    if(log_file == None):
        print_status=True
        print("Verbose mode")
    else:
        print_status=False
        print("Logging to "+str(log_file))
        f = open(log_file, 'w')

    while current_date + pd.offsets.Hour(PERIOD) + pd.offsets.Hour(PREDICTION) <= date_max:
        # train is the dataframe of 0-24 h
        train_window = df[ (df['datetime'] <= current_date + pd.offsets.Hour(PERIOD)) & (df['datetime'] > current_date) ]
        # pred is the dataframe of 24-24+1 h
        test_window  = df[ (df['datetime'] <= current_date  + pd.offsets.Hour(PERIOD) + pd.offsets.Hour(PREDICTION)) & (df['datetime'] > current_date + pd.offsets.Hour(PERIOD))  ]
                # check if train windows is empty
        if (train_window.empty):
            if(print_status):
                print("Df train was empty with initial date = "+str(current_date))    
            else:
                f.write("Df train was empty with initial date = "+str(current_date))
                f.write("\n")
            current_date +=  pd.offsets.Hour(PREDICTION)
            continue
        # check if test windows is empty
        if (test_window.empty):
            if(print_status):
                print("Df test was empty with initial date = "+str(current_date))    
            else:
                f.write("Df test was empty with initial date = "+str(current_date))
                f.write("\n")
            current_date +=  pd.offsets.Hour(PREDICTION)
            continue
        # check if anomalies are present in test
        if((train_window['validation_code'].values != 1).any()):
            if(print_status):
                print("Df was containing anomalies at initial date = "+str(current_date))    
            else:
                f.write("Df was containing anomalies at initial date = "+str(current_date))
                f.write("\n")
            current_date +=  pd.offsets.Hour(PREDICTION)
            continue

        header={
            'sensor_code':train_window['label'].values[0],
            'in_datetime':train_window['datetime'].values[0],
        }

        features = train_window['value'].reset_index(drop=True).to_dict()

        target =  test_window['value'].reset_index(drop=True).to_dict()
        val_label = test_window['validation_code'].reset_index(drop=True)
        n_labels = len(val_label)
        val_label.index = [f"val_{idx}" for idx in val_label.index] 
        val_label = val_label.to_dict()
        # if either features is empty or target, continue
        data_train.append({**header,**features})
        data_test.append({**header,**target,**val_label})

        i = i + 1
        if(i%print_every ==0):
            if(print_status):
                print("index = "+str(i)+"\t current date = "+str(current_date)+"\t to the end date = "+str(date_max))
            else:
                print("index = "+str(i)+"\t current date = "+str(current_date)+"\t to the end date = "+str(date_max))
                f.write("index = "+str(i)+"\t current date = "+str(current_date)+"\t to the end date = "+str(date_max))
                f.write("\n")
        current_date +=  pd.offsets.Hour(PREDICTION)

    if(len(data_train) == 0):
        print("Unable to create a dataframe with this time division, data is missing")
        if(not print_status):
            f.write("Unable to process this station with this time division, data is missing")
            f.write("\n")
        return -1, -1, -1
        
    df_train = pd.DataFrame(data_train)
    df_test = pd.DataFrame(data_test)

    # remove data with NaN in training
    bad_rows = df_train.isnull().values.any(axis=1)
    df_train = df_train.iloc[~bad_rows]
    df_test = df_test.iloc[~bad_rows]

    bad_rows = df_test.isnull().values.any(axis=1)
    df_train = df_train.iloc[~bad_rows].reset_index(drop=True)
    df_test = df_test.iloc[~bad_rows].reset_index(drop=True)
    # bad_rows = pd.isnull(df_test).any(1).to_numpy().nonzero()[0]
    # df_train = df_train.drop(labels=bad_rows,axis=0).reset_index(drop=True)
    # df_test = df_test.drop(labels=bad_rows,axis=0).reset_index(drop=True)

    # close the log file if printing is note selected
    if(not print_status):
        f.close()

    return df_train,df_test,n_labels

def split_multiple_df_for_TSF(df, list_sensor_label, PERIOD, PREDICTION, print_every = 500, log_file=None):
    """
    Split the dataframe df in train and test, for multiple LSTM.
    @df: the dataframe, must have a datetime field
    @PERIOD: is the dimension of the train (in hours)
    @PREDICTION: is the dimension of the test (in hours)
    @print_every: how many element to process before printing
    @log_file: where the log file should be stored. If none is provided, the warning are printed on screen.

    for each datetime starting from the minimum in the dataframe,
    split the dataframe in 
    train = df[current_time, current_time + PERIOD]
    and 
    test = df[current_time + PERIOD, current_time + PERIOD + PREDICTION]

    finally return the train and the test and the number of points to be predicted. 
    
    """    
    date_min = df['datetime'].min()
    date_max = df['datetime'].max()
    current_date = date_min
    i = 0
    data_train = []
    data_test = []
    print_status=True
    if(log_file == None):
        print_status=True
        print("Verbose mode")
    else:
        print_status=False
        print("Logging to "+str(log_file))
        f = open(log_file, 'w')

    while current_date + pd.offsets.Hour(PERIOD) + pd.offsets.Hour(PREDICTION) <= date_max:
        # train is the dataframe of 0-24 h
        train_window = df[ (df['datetime'] <= current_date + pd.offsets.Hour(PERIOD)) & (df['datetime'] > current_date) ]
        # pred is the dataframe of 24-24+1 h
        test_window  = df[ (df['datetime'] <= current_date  + pd.offsets.Hour(PERIOD) + pd.offsets.Hour(PREDICTION)) & (df['datetime'] > current_date + pd.offsets.Hour(PERIOD))  ]
                # check if train windows is empty
        if (train_window.empty):
            if(print_status):
                print("Df train was empty with initial date = "+str(current_date))    
            else:
                f.write("Df train was empty with initial date = "+str(current_date))
                f.write("\n")
            current_date +=  pd.offsets.Hour(PREDICTION)
            continue
        # check if test windows is empty
        if (test_window.empty):
            if(print_status):
                print("Df test was empty with initial date = "+str(current_date))    
            else:
                f.write("Df test was empty with initial date = "+str(current_date))
                f.write("\n")
            current_date +=  pd.offsets.Hour(PREDICTION)
            continue
                
        # check if anomalies are present in test
        if((train_window[[f'validation_code_{sensor}' for sensor in list_sensor_label]].values != 1).any()):
            if(print_status):
                print("Df was containing anomalies at initial date = "+str(current_date))    
            else:
                f.write("Df was containing anomalies at initial date = "+str(current_date))
                f.write("\n")
            current_date +=  pd.offsets.Hour(PREDICTION)
            continue

        header={
            'sensor_code':list_sensor_label,
            'in_datetime':train_window['datetime'].values[0],
        }

        # features = train_window['value'].reset_index(drop=True).to_dict()
        # print(train_window[[f'value_{sensor}' for sensor in list_sensor_label]].reset_index(drop=True).to_dict())
        features = {}
        j = 0
        for list_values in train_window[[f'value_{sensor}' for sensor in list_sensor_label]].reset_index(drop=True).values:
          features[j] = list(list_values)
          j+=1

        target = {}
        j = 0
        for list_values in test_window[[f'value_{sensor}' for sensor in list_sensor_label]].reset_index(drop=True).values:
          target[j] = list(list_values)
          j+=1
        
        val_label = {}
        j = 0
        for list_values in test_window[[f'validation_code_{sensor}' for sensor in list_sensor_label]].reset_index(drop=True).values:
          val_label[f"val_{j}"] = list(list_values)
          j+=1

        # if either features is empty or target, continue
        data_train.append({**header,**features})
        data_test.append({**header,**target,**val_label})

        i = i + 1
        if(i%print_every ==0):
            if(print_status):
                print("index = "+str(i)+"\t current date = "+str(current_date)+"\t to the end date = "+str(date_max))
            else:
                f.write("index = "+str(i)+"\t current date = "+str(current_date)+"\t to the end date = "+str(date_max))
                f.write("\n")
        current_date +=  pd.offsets.Hour(PREDICTION)

    if(len(data_train) == 0):
        print("Unable to create a dataframe with this time division, data is missing")
        if(not print_status):
            f.write("Unable to process this station with this time division, data is missing")
            f.write("\n")
        return -1, -1, -1
        
    df_train = pd.DataFrame(data_train)
    df_test = pd.DataFrame(data_test)

    # remove data with NaN in training
    ### TODO: UPDATE WITH LAST CHANGES BY PIERO
    bad_rows = df_train.isnull().values.any(axis=1)
    df_train = df_train.iloc[~bad_rows]
    df_test = df_test.iloc[~bad_rows]

    bad_rows = df_test.isnull().values.any(axis=1)
    df_train = df_train.iloc[~bad_rows].reset_index(drop=True)
    df_test = df_test.iloc[~bad_rows].reset_index(drop=True)
        
    # bad_rows = pd.isnull(df_test).any(1).to_numpy().nonzero()[0]
    # df_train = df_train.drop(labels=bad_rows,axis=0).reset_index(drop=True)
    # df_test = df_test.drop(labels=bad_rows,axis=0).reset_index(drop=True)

    # close the log file if printing is note selected
    if(not print_status):
        f.close()

    # j is equal to the number of previsions to be done
    return df_train,df_test,j

