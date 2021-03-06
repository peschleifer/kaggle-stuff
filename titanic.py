# Started with the dataquest tutorial
from sklearn import cross_validation
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.feature_selection import SelectKBest, f_classif
# Import the linear regression class
from sklearn.linear_model import LinearRegression, LogisticRegression
# Sklearn also has a helper that makes it easy to do cross validation
from sklearn.cross_validation import KFold
import numpy as np
import matplotlib.pyplot as plt
import operator
import pandas
import re
from numpy import unique

# A function to get the title from a name.
def get_title(name):
    # Use a regular expression to search for a title.  Titles always consist of capital and lowercase letters, and end with a period.
    title_search = re.search(' ([A-Za-z]+)\.', name)
    # If the title exists, extract and return it.
    if title_search:
        return title_search.group(1)
    return ""

# A dictionary mapping family name to id
family_id_mapping = {}

# A function to get the id given a row
def get_family_id(row):
    # Find the last name by splitting on a comma
    last_name = row["Name"].split(",")[0]
    # Create the family id
    family_id = "{0}{1}".format(last_name, row["FamilySize"])
    # Look up the id in the mapping
    if family_id not in family_id_mapping:
        if len(family_id_mapping) == 0:
            current_id = 1
        else:
            # Get the maximum id from the mapping and add one to it if we don't have an id
            current_id = (max(family_id_mapping.items(), key=operator.itemgetter(1))[1] + 1)
        family_id_mapping[family_id] = current_id
    return family_id_mapping[family_id]

# First let's make a function to sort through the sex 
def male_female_child(passenger):
    # 0 = Male
    # 1 = Female
    # -1 = Child
    
    # Take the Age and Sex
    age,sex = passenger
    # Compare the age, otherwise leave the sex
    if age < 16:
        return -1
    else:
        return sex
    
titanic = pandas.read_csv("titanic/train.csv")
titanic_test = pandas.read_csv("titanic/test.csv")

def loadTrain():
    # We can use the pandas library in python to read in the csv file.
    # This creates a pandas dataframe and assigns it to the titanic variable.
    
    print titanic.describe()
    # Print the first 5 rows of the dataframe.
    print titanic.head(5)
    
    # The titanic variable is available here.
    titanic["Age"] = titanic["Age"].fillna(titanic["Age"].median())
    
    # Find all the unique genders -- the column appears to contain only male and female.
    print titanic["Sex"].unique()
    
    # Replace all the occurences of male with the number 0.
    titanic.loc[titanic["Sex"] == "male", "Sex"] = 0
    titanic.loc[titanic["Sex"] == "female", "Sex"] = 1
    
    # Find all the unique values for "Embarked".
    print titanic["Embarked"].unique()
    titanic["Embarked"] = titanic["Embarked"].fillna("S")
    titanic.loc[titanic["Embarked"] == "S", "Embarked"] = 0
    titanic.loc[titanic["Embarked"] == "C", "Embarked"] = 1
    titanic.loc[titanic["Embarked"] == "Q", "Embarked"] = 2

def tryRegression():
 
    # The columns we'll use to predict the target
    predictors = ["Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked"]
    
    # Try linear regression first
    # Initialize our algorithm class
    alg = LinearRegression()
    # Generate cross validation folds for the titanic dataset.  It return the row indices corresponding to train and test.
    # We set random_state to ensure we get the same splits every time we run this.
    kf = KFold(titanic.shape[0], n_folds=3, random_state=1)
    
    predictions = []
    for train, test in kf:
        # The predictors we're using the train the algorithm.  Note how we only take the rows in the train folds.
        train_predictors = (titanic[predictors].iloc[train,:])
        # The target we're using to train the algorithm.
        train_target = titanic["Survived"].iloc[train]
        # Training the algorithm using the predictors and target.
        alg.fit(train_predictors, train_target)
        # We can now make predictions on the test fold
        test_predictions = alg.predict(titanic[predictors].iloc[test,:])
        predictions.append(test_predictions)
    
    
    # The predictions are in three separate numpy arrays.  Concatenate them into one.  
    # We concatenate them on axis 0, as they only have one axis.
    predictions = np.concatenate(predictions, axis=0)
    
    # Map predictions to outcomes (only possible outcomes are 1 and 0)
    predictions[predictions > .5] = 1
    predictions[predictions <=.5] = 0
    #accuracy = (predictions * titanic["Survived"]).sum()/len(predictions)
    accuracy = sum([titanic["Survived"][i] == predictions[i] for i in range(len(predictions))])/float(len(predictions))
    print "Linear regression:", accuracy
    
    # Now try logistic regression
    # Initialize our algorithm
    alg = LogisticRegression(random_state=1)
    # Compute the accuracy score for all the cross validation folds.  (much simpler than what we did before!)
    scores = cross_validation.cross_val_score(alg, titanic[predictors], titanic["Survived"], cv=3)
    # Take the mean of the scores (because we have one for each fold)
    print scores.mean()
    
    titanic_test["Age"] = titanic_test["Age"].fillna(titanic["Age"].median())
    titanic_test.loc[titanic_test["Sex"] == "male", "Sex"] = 0
    titanic_test.loc[titanic_test["Sex"] == "female", "Sex"] = 1
    titanic_test["Embarked"] = titanic_test["Embarked"].fillna("S")
    titanic_test.loc[titanic_test["Embarked"] == "S", "Embarked"] = 0
    titanic_test.loc[titanic_test["Embarked"] == "C", "Embarked"] = 1
    titanic_test.loc[titanic_test["Embarked"] == "Q", "Embarked"] = 2
    titanic_test["Fare"] = titanic_test["Fare"].fillna(titanic["Fare"].median())
    
    # Initialize the algorithm class
    alg = LogisticRegression(random_state=1)
    
    # Train the algorithm using all the training data
    alg.fit(titanic[predictors], titanic["Survived"])
    
    # Make predictions using the test set.
    predictions = alg.predict(titanic_test[predictors])
    
    # Create a new dataframe with only the columns Kaggle wants from the dataset.
    submission = pandas.DataFrame({
            "PassengerId": titanic_test["PassengerId"],
            "Survived": predictions
        })
    submission.to_csv("kaggle-r.csv", index=False)

def tryEnsembling():
    
    predictors = ["Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked"]
    
    # Initialize our algorithm with the default paramters
    # n_estimators is the number of trees we want to make
    # min_samples_split is the minimum number of rows we need to make a split
    # min_samples_leaf is the minimum number of samples we can have at the place where a tree branch ends (the bottom points of the tree)
    alg = RandomForestClassifier(random_state=1, n_estimators=10, min_samples_split=2, min_samples_leaf=1)
    scores = cross_validation.cross_val_score(alg, titanic[predictors], titanic["Survived"], cv=3)
    print "random forest score", scores.mean()
    
    # Generating a familysize column
    titanic["FamilySize"] = titanic["SibSp"] + titanic["Parch"]
    
    # The .apply method generates a new series
    titanic["NameLength"] = titanic["Name"].apply(lambda x: len(x))
    
    
    # Get all the titles and print how often each one occurs.
    titles = titanic["Name"].apply(get_title)
    print pandas.value_counts(titles)
    
    # Map each title to an integer.  Some titles are very rare, and are compressed into the same codes as other titles.
    title_mapping = {"Mr": 1, "Miss": 2, "Mrs": 3, "Master": 4, "Dr": 5, "Rev": 6, "Major": 7, "Col": 7, "Mlle": 8, "Mme": 8, "Don": 9, "Lady": 10, "Countess": 10, "Jonkheer": 10, "Sir": 9, "Capt": 7, "Ms": 2}
    for k,v in title_mapping.items():
        titles[titles == k] = v
    
    # Verify that we converted everything.
    #print pandas.value_counts(titles)
    
    # Add in the title column.
    titanic["Title"] = titles 

    # We'll define a new column called 'person', remember to specify axis=1 for columns and not index
    titanic['person'] = titanic[['Age','Sex']].apply(male_female_child,axis=1)
    
    # Get the family ids with the apply method
    family_ids = titanic.apply(get_family_id, axis=1)
      
    
    # Print the count of each unique id.
    #print pandas.value_counts(family_ids)
    
    # Try number of women in family, number of children?
    titanic["FamilyId"] = family_ids
    titanic["numbWomen"] = 0
    titanic["numbChildren"] = 0

    for f in unique(family_ids):
        w = len(titanic[((titanic.FamilyId == f) & (titanic.person == 1))].index)
        titanic.loc[titanic["FamilyId"] == f,"numbWomen"] = w
        titanic.loc[titanic["FamilyId"] == f,"numbChildren"] = len(titanic[((titanic.FamilyId == f) & (titanic.person == -1))].index)

    # There are a lot of family ids, so we'll compress all of the families under 3 members into one code.
    # Note that we do not do this until after we have calculated the number of woman and children in the family
    family_ids[titanic["FamilySize"] < 3] = -1
    titanic["FamilyId"] = family_ids


    predictors = ["Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked", "FamilySize", "Title", "FamilyId", "numbWomen", "numbChildren"]
    
    # Perform feature selection
    selector = SelectKBest(f_classif, k=5)
    selector.fit(titanic[predictors], titanic["Survived"])
    
    # Get the raw p-values for each feature, and transform from p-values into scores
    scores = -np.log10(selector.pvalues_)
    
    # Plot the scores.  See how "Pclass", "Sex", "Title", and "Fare" are the best?
    plt.bar(range(len(predictors)), scores)
    plt.xticks(range(len(predictors)), predictors, rotation='vertical')
    plt.show()

    
    # Pick only the four best features.
    predictors = ["Pclass", "Sex", "Fare", "Title"]
    # Number of women in family seems a better predictor than fare
    predictors = ["Pclass", "Sex", "numbWomen", "Title"]
  
    alg = RandomForestClassifier(random_state=1, n_estimators=150, min_samples_split=8, min_samples_leaf=4)
    print 'alg set'
    scores = cross_validation.cross_val_score(alg, titanic[predictors], titanic["Survived"], cv=3)
    print "Random forest score with numbWomen replacing Fare", scores.mean()
    
    # The algorithms we want to ensemble.
    # We're using the more linear predictors for the logistic regression, and everything with the gradient boosting classifier.
    algorithms = [
        #[GradientBoostingClassifier(random_state=1, n_estimators=25, max_depth=3), ["Pclass", "Sex", "Age", "numbWomen", "Fare", "Embarked", "FamilySize", "Title", "FamilyId"]],
        [GradientBoostingClassifier(random_state=1, n_estimators=25, max_depth=3), ["Pclass", "Sex", "Age", "numbWomen", "Fare", "Embarked", "Title", "FamilyId"]],
        [LogisticRegression(random_state=1), ["Pclass", "Sex", "Fare","numbWomen", "FamilySize", "Title", "Age", "Embarked"]]
    ]
    
    # Initialize the cross validation folds
    kf = KFold(titanic.shape[0], n_folds=3, random_state=1)
    
    predictions = []
    for train, test in kf:
        train_target = titanic["Survived"].iloc[train]
        full_test_predictions = []
        # Make predictions for each algorithm on each fold
        for alg, predictors in algorithms:
            # Fit the algorithm on the training data.
            alg.fit(titanic[predictors].iloc[train,:], train_target)
            # Select and predict on the test fold.  
            # The .astype(float) is necessary to convert the dataframe to all floats and avoid an sklearn error.
            test_predictions = alg.predict_proba(titanic[predictors].iloc[test,:].astype(float))[:,1]
            full_test_predictions.append(test_predictions)
        # Use a simple ensembling scheme -- just average the predictions to get the final classification.
        test_predictions = (full_test_predictions[0] + full_test_predictions[1]) / 2
        # Any value over .5 is assumed to be a 1 prediction, and below .5 is a 0 prediction.
        test_predictions[test_predictions <= .5] = 0
        test_predictions[test_predictions > .5] = 1
        predictions.append(test_predictions)
    
    # Put all the predictions together into one array.
    predictions = np.concatenate(predictions, axis=0)
    
    # Compute accuracy by comparing to the training data.
    accuracy = sum(predictions[predictions == titanic["Survived"]]) / float(len(predictions))
    print "Accuracy:",accuracy
    
    # First, we'll add titles to the test set.
    titles = titanic_test["Name"].apply(get_title)
    # We're adding the Dona title to the mapping, because it's in the test set, but not the training set
    title_mapping = {"Mr": 1, "Miss": 2, "Mrs": 3, "Master": 4, "Dr": 5, "Rev": 6, "Major": 7, "Col": 7, "Mlle": 8, "Mme": 8, "Don": 9, "Lady": 10, "Countess": 10, "Jonkheer": 10, "Sir": 9, "Capt": 7, "Ms": 2, "Dona": 10}
    for k,v in title_mapping.items():
        titles[titles == k] = v
    titanic_test["Title"] = titles
    # Check the counts of each unique title.
    #print pandas.value_counts(titanic_test["Title"])
    
    # Now, we add the family size column.
    titanic_test["FamilySize"] = titanic_test["SibSp"] + titanic_test["Parch"]
    
    # Now we can add family ids.
    # We'll use the same ids that we did earlier.
    #print family_id_mapping
    
    titanic_test['person'] = titanic_test[['Age','Sex']].apply(male_female_child,axis=1)
    family_ids = titanic_test.apply(get_family_id, axis=1)
    titanic_test["FamilyId"] = family_ids
    titanic_test["numbWomen"] = 0
    titanic_test["numbChildren"] = 0

    for f in unique(family_ids):
        w = len(titanic_test[((titanic_test.FamilyId == f) & (titanic_test.person == 1))].index)
        titanic_test.loc[titanic_test["FamilyId"] == f,"numbWomen"] = w
        titanic_test.loc[titanic_test["FamilyId"] == f,"numbChildren"] = len(titanic_test[((titanic_test.FamilyId == f) & (titanic_test.person == -1))].index)

    family_ids[titanic_test["FamilySize"] < 3] = -1
    titanic_test["FamilyId"] = family_ids
    titanic_test["NameLength"] = titanic_test["Name"].apply(lambda x: len(x))
    
    #predictors = ["Pclass", "Sex", "Age", "numbWomen", "Fare", "Embarked", "FamilySize", "Title", "FamilyId"]
    predictors = ["Pclass", "Sex", "Age", "numbWomen", "Fare", "Embarked",  "Title", "FamilyId"]
    
    algorithms = [
        [GradientBoostingClassifier(random_state=1, n_estimators=25, max_depth=3), predictors],
        #[LogisticRegression(random_state=1), ["Pclass", "Sex", "Fare", "FamilySize", "Title", "Age", "numbWomen", "Embarked"]]
        [LogisticRegression(random_state=1), ["Pclass", "Sex", "Fare", "numbWomen", "Title", "Age", "numbWomen", "Embarked"]]
    ]
    
    full_predictions = []
    for alg, predictors in algorithms:
        # Fit the algorithm using the full training data.
        alg.fit(titanic[predictors], titanic["Survived"])
        # Predict using the test dataset.  We have to convert all the columns to floats to avoid an error.
        predictions = alg.predict_proba(titanic_test[predictors].astype(float))[:,1]
        full_predictions.append(predictions)
    
    # The gradient boosting classifier generates better predictions, so we weight it higher.
    predictions = (full_predictions[0] * 3 + full_predictions[1]) / 4
    predictions[predictions <= .5] = 0
    predictions[predictions > .5] = 1
    predictions = predictions.astype(int)
    submission = pandas.DataFrame({'PassengerId':titanic_test["PassengerId"],'Survived':predictions})
    submission.to_csv("kaggle.csv", index=False)

if __name__ == '__main__':
    loadTrain()
    tryRegression()
    tryEnsembling()
    