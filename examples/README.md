# Fictional café reviews

`fictional_cafe_reviews.csv` contains the same ten fictional reviews as the
unchanged M2 dataset in `experiments/reviews.json`. They cover English, French,
German and Luxembourgish. This is test data, not feedback collected from customers.

Upload the CSV using **Upload CSV** in ReviewWise. It uses UTF-8 with a BOM for
Windows/Excel compatibility and a single column named `review`.

Manual reference counts: slow service 3; cold coffee 2; high prices 2; dirty
tables, incorrect order and unfriendly staff 1 each. The model may miss or
misclassify these; compare its actual evidence with the original review text.
These reference answers are not included in the AI input.
