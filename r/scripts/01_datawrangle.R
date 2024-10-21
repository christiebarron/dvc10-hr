library(tidyverse)

df <- readr::read_delim(file = "data/raw/HRDataset_v14.xls.txt", delim = "\t", locale = locale(encoding = "UTF-16"))

df %>% 
  group_by(Employee_Name) %>% 
  summarise(unique())


unique(df$Employee_Name)
colnames(df)

psych::describeBy(df, "Employee_Name")

?read_tsv
