object_type: metric_calc
unique_name: "Sales Electronics"
label: "Sales Electronics"
expression: |
  ([Measures].[Sales Amount], [Product].[Category].[Electronics])
provenance:
  source_file: "Sales.tmdl"
  source_dax: |
    CALCULATE(SUM(Sales[Amount]), Product[Category] = "Electronics")
  source_line: 1
