import pandas as pd
import pickle
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler, OneHotEncoder 
from sklearn.compose import ColumnTransformer
from sklearn.base import BaseEstimator, TransformerMixin

pd.set_option('future.no_silent_downcasting', True)

df_train = pd.read_csv('https://raw.githubusercontent.com/Murcha1990/MLDS_ML_2022/main/Hometasks/HT1/cars_train.csv')
df_test = pd.read_csv('https://raw.githubusercontent.com/Murcha1990/MLDS_ML_2022/main/Hometasks/HT1/cars_test.csv')
    
class Preprocessing(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.seats_median = None
        self.median_dict = dict()
    
    @staticmethod
    def to_float(x):
            try:
                return float(x.split()[0])
            except:
                return None
            
    def fit(self, X, y=None):
        self.seats_median = X['seats'].median()
            
        for col_name in ['mileage', 'engine', 'max_power']:
            X[col_name] = X[col_name].apply(self.to_float)
            self.median_dict[col_name] = X[col_name].median()
        
        # drop_and_duplicated = X.drop('selling_price', axis=1).duplicated()
        # no_target_dup = X[drop_and_duplicated]
        # X = X.drop(no_target_dup.index).reset_index(drop=True)
        # y = y.drop(no_target_dup.index).reset_index(drop=True)
        
        no_target_dup = X[X.duplicated()]
        X = X.drop(no_target_dup.index).reset_index(drop=True)
        y = y.drop(no_target_dup.index).reset_index(drop=True)
        
        return self
    
    
    def transform(self, X):
        X_copy = X.copy()
        
        X_copy['seats'] = X_copy['seats'].fillna(self.seats_median)
            
        for col_name in ['mileage', 'engine', 'max_power']:
            X_copy[col_name] = X_copy[col_name].apply(self.to_float)
            X_copy[col_name] = X_copy[col_name].fillna(self.median_dict[col_name])


        X_copy = X_copy.drop('torque', axis=1)

        for col_name in ['engine', 'seats']:
            X_copy[col_name] = X_copy[col_name].astype(int)
            
        return X_copy


class NameTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, min_count):
        self.min_count = min_count
        self.popular_name_list = None
    
    def fit(self, X, y=None):
        X_copy = X.copy()
        X_copy['name_count'] = X_copy.groupby(by='name').transform('count')['year']
        self.popular_name_list = X_copy[X_copy['name_count'] > self.min_count]['name'].unique()
        return self

    def transform(self, X):
        X_copy = X.copy()
        
        def is_popular(x):
            if x in self.popular_name_list:
                return x
            else:
                return 'other'

        X_copy['popular_name'] = X_copy['name'].apply(is_popular)
        X_copy = X_copy.drop('name', axis=1)
        
        return X_copy

def train_and_dump():
    prep = Preprocessing()
    
    X_train = df_train.drop('selling_price', axis=1)
    X_test = df_test.drop('selling_price', axis=1)
    
    y_train = df_train['selling_price']
    y_test = df_test['selling_price']
    
    numeric=['year', 'km_driven', 'mileage', 'engine', 'max_power']
    categorical = ['fuel', 'seller_type', 'transmission', 'owner', 'popular_name', 'seats']

    ct = ColumnTransformer([
        ('scale', StandardScaler(), numeric),
        ('ohe', OneHotEncoder(drop='first'), categorical)
        ])

    pipe = Pipeline([
        ('preprocessing', Preprocessing()),
        ('name to popular_name', NameTransformer(20)),
        ('scale + ohe', ct),
        ('ridge', Ridge())
    ])

    pipe.fit(X_train, y_train)

    with open('model.pkl', 'wb') as file:
        pickle.dump(pipe, file)

    # with open('model.pkl', 'rb') as file:
    #     loaded_model = pickle.load(file)

if __name__ == '__main__':
    train_and_dump()