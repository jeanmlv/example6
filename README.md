# example6

> setwd("/domino")
> # Diretório atual dos datasets
> data_dir <- "/domino/datasets/local/clinical-trial-data/CNTO1959UCO3001-QUASAR-LTE-WK188/load-3296/Data/_csv"
> 
> # Identificar arquivos CSV
> files <- list.files(
+   data_dir,
+   pattern = "\\.csv$",
+   full.names = TRUE,
+   ignore.case = TRUE
+ )
> 
> # Termos relacionados a vídeos e avaliações
> keywords <- paste(
+   c(
+     "VIDEO", "IMAGE", "IMAGING",
+     "ENDOS", "RECORD", "MEDIA",
+     "FILE", "UPLOAD", "CONSENT",
+     "CENTRAL", "READ", "VISIT"
+   ),
+   collapse = "|"
+ )
> 
> # Procurar colunas relevantes em todos os ADaM
> results <- lapply(files, function(f) {
+   
+   cols <- names(
+     read.csv(f, nrows = 0, check.names = FALSE)
+   )
+   
+   matched <- cols[
+     grepl(keywords, cols, ignore.case = TRUE)
+   ]
+   
+   if (length(matched) == 0) return(NULL)
+   
+   data.frame(
+     DATASET = basename(f),
+     VARIABLE = matched
+   )
+ })
> 
> results <- Filter(Negate(is.null), results)
> 
> if (length(results) > 0) {
+   output <- do.call(rbind, results)
+   print(output, row.names = FALSE)
+   write.csv(
+     output,
+     "quasar_video_metadata_candidates.csv",
+     row.names = FALSE
+   )
+ } else {
+   cat("No matching variable names found.\n")
+ }
      DATASET VARIABLE
  adcssrs.csv   AVISIT
  adcssrs.csv  AVISITN
  adcssrs.csv    VISIT
  adcssrs.csv VISITNUM
 adcssrsi.csv   AVISIT
 adcssrsi.csv  AVISITN
    adeff.csv   AVISIT
    adeff.csv  AVISITN
   adeffo.csv   AVISIT
   adeffo.csv  AVISITN
     adex.csv VISITDOS
     adex.csv   AVISIT
     adex.csv  AVISITN
     adex.csv    VISIT
     adex.csv VISITNUM
   adhist.csv   AVISIT
   adhist.csv  AVISITN
   adhist.csv    VISIT
   adhist.csv VISITNUM
  adhisti.csv   AVISIT
  adhisti.csv  AVISITN
  adhisti.csv    VISIT
  adhisti.csv VISITNUM
   adibdq.csv   AVISIT
   adibdq.csv  AVISITN
   adibdq.csv    VISIT
   adibdq.csv VISITNUM
  adibdqi.csv   AVISIT
  adibdqi.csv  AVISITN
  adibdqi.csv    VISIT
  adibdqi.csv VISITNUM
     adlb.csv   AVISIT
     adlb.csv  AVISITN
     adlb.csv    VISIT
     adlb.csv VISITNUM
   adlbef.csv   AVISIT
   adlbef.csv  AVISITN
   adlbef.csv    VISIT
   adlbef.csv VISITNUM
  adlbtox.csv   AVISIT
   admayo.csv   AVISIT
   admayo.csv  AVISITN
   admayo.csv    VISIT
   admayo.csv VISITNUM
  admayoi.csv   AVISIT
  admayoi.csv  AVISITN
  admayoi.csv    VISIT
  admayoi.csv VISITNUM
 adpromis.csv   AVISIT
 adpromis.csv  AVISITN
 adpromis.csv    VISIT
 adpromis.csv VISITNUM
 adpromsi.csv   AVISIT
 adpromsi.csv  AVISITN
 adpromsi.csv    VISIT
 adpromsi.csv VISITNUM
    adsaf.csv   AVISIT
    adsaf.csv  AVISITN
  advcort.csv   AVISIT
  advcort.csv  AVISITN
  advcort.csv    VISIT
  advcort.csv VISITNUM
     advs.csv   AVISIT
     advs.csv  AVISITN
     advs.csv    VISIT
     advs.csv VISITNUM
 advscort.csv   AVISIT
 advscort.csv  AVISITN
 advscort.csv    VISIT
 advscort.csv VISITNUM
   adwpai.csv   AVISIT
   adwpai.csv  AVISITN
   adwpai.csv    VISIT
   adwpai.csv VISITNUM
Error in file(file, ifelse(append, "a", "w")) : 
  cannot open the connection
In addition: Warning message:
In file(file, ifelse(append, "a", "w")) :
 
 Error in file(file, ifelse(append, "a", "w")) : 
  cannot open the connection 
