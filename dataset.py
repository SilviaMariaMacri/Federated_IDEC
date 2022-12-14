from tensorflow.keras.datasets import mnist
import numpy as np
import random 


def load_mnist(binary_threshold=None):
    
    (x_train, y_train), (x_test, y_test) = mnist.load_data()
    x = np.concatenate((x_train, x_test))
    y = np.concatenate((y_train, y_test))
    x = x.reshape((x.shape[0], -1))
    x = np.divide(x, 255.)
    #binary
    if binary_threshold is not None:
        x =np.where(x>binary_threshold,1,0) 
    return x, y 



def create_federated_dataset(x,y,
                             num_clients=8,
                             samples_per_cluster_per_client=300,
                             seed=0):
    
    samples_per_cluster = int(samples_per_cluster_per_client*num_clients)
    n_clusters = len(np.unique(y))
    index = np.array([])
    index_fed = []
    for i in range(n_clusters):
        
        index_i = np.argwhere(y==i)
        index_i = index_i.reshape((1,len(index_i)))[0]
        index_i = index_i[0:samples_per_cluster]
        #index = np.concatenate([index,index_i])
        #index = index.astype(int)
        index_i_splitted = np.split(index_i,num_clients)
        index_i_splitted = list(map(list,index_i_splitted))
        index_fed.append(index_i_splitted)
    #y_centr = y[index]
    #x_centr = x[index]
    
    index_fed = np.array(index_fed)
    x_fed = []
    y_fed = []
    for i in range(num_clients):
        index_fed_i = index_fed[:,i]
        index_fed_i = index_fed_i.reshape((1,samples_per_cluster_per_client*n_clusters))[0]
        random.Random(seed).shuffle(index_fed_i)
        x_fed.append(x[index_fed_i])
        y_fed.append(y[index_fed_i])
        
    return x_fed,y_fed



def from_fed_to_centr(x_fed,y_fed=None):
    n_clients = len(x_fed)
    x_centr = x_fed[0].copy()
    if y_fed != None:
        y_centr = y_fed[0].copy()
    else:
        y_centr = None
    for i in range(1,n_clients):
        x_centr = np.concatenate([x_centr,x_fed[i]])
        if y_fed != None:
            y_centr = np.concatenate([y_centr,y_fed[i]])
    return x_centr,y_centr


def missing_data_distribution(x_fed,
                              nan_fraction=0.375, #frazione di nan per dimensione
                              nan_dims = [0], 
                              client_with_missing_data=8, #[int,list]
                              nan_substitute = 'mean',
                              seed=None,
                              setting='federated'):


    if nan_substitute == 'mean':
        criterion = 'mean'
    else:
        criterion = 'number'
    if setting == 'federated':
        num_clients = len(x_fed)
        num_samples_per_client = len(x_fed[0])
        num_samples = len(x_fed[0])*len(x_fed)        
    else:
        num_clients = 1
        num_samples = len(x_fed)
        num_samples_per_client = num_samples
        client_with_missing_data = [0]

    sample_index = np.arange(num_samples_per_client)
    
    if isinstance(client_with_missing_data,int):
        if seed is not None:
            np.random.seed(seed)
        client_with_missing_data = np.random.choice(np.arange(num_clients),client_with_missing_data,replace=False)
        print('client_with_missing_data',client_with_missing_data)
    nan_per_client = int((num_samples*nan_fraction)/len(client_with_missing_data))
    x_fed_nan = []
    nan_index_list = []
    for i in range(num_clients):    
        if setting == 'federated':
            x_client = x_fed[i].copy()
        else:
            x_client = x_fed.copy()
        x_client = x_client.astype(float)
            
        if i not in client_with_missing_data:
            x_fed_nan.append(x_client)
            continue
            
        for k in nan_dims:
            if seed is not None:
                np.random.seed(seed+i+k)
            #print(seed+i+k)
            nan_index = np.random.choice(sample_index,size=nan_per_client,replace=False) 
            dim_with_nan = np.delete(x_client[:,k],nan_index)
            if criterion == 'mean':
                nan_substitute = np.mean(dim_with_nan)
            for j in nan_index:
                x_client[j,k] = nan_substitute
        # ha senso metterlo qui se inserisci nan in una dimensione alla volta:
        nan_index_list.append(nan_index)
        x_fed_nan.append(x_client)
        
    return x_fed_nan#,nan_index_list
    

def dim_choice(x_centr,threshold=12700):
    
    count_values = x_centr.sum(axis=0)
    x_centr_condition = (count_values>threshold)
    index_dim_nan = np.where(x_centr_condition)

    mean_list = []
    for i in index_dim_nan[0]:
        mean_list.append(x_centr[:,i].mean())     
        
    return index_dim_nan[0],mean_list   
