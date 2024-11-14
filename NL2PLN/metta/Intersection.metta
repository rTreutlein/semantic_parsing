;; Define the intersect function
(= (intersect $xs $ys)
   (if (== $xs ())
       ()
       (let* (($x (car-atom $xs))
              ($rest (cdr-atom $xs)))
         (if (contains? $ys $x)
             (let $r (intersect $rest $ys) (cons-atom $x $r))
             (intersect $rest $ys)))))

;; Helper function to check if an element is in an expression
(= (contains? $ys $x)
   (if (== $ys ())
       False
       (let $y (car-atom $ys)
       (if (== $x $y)
           True
           (contains? (cdr-atom $ys) $x)))))

;; Define the inverse-intersect function                                                                                                                             
 (= (inverse-intersect $xs $ys)                                                                                                                                       
    (let* (($intersection (intersect $xs $ys))                                                                                                                        
           ($diff-xs (difference2 $xs $intersection))                                                                                                                  
           ($diff-ys (difference2 $ys $intersection)))                                                                                                                 
      (append $diff-xs $diff-ys)))                                                                                                                                    
  
;; Helper function to get the difference between two expressions
(= (difference2 $xs $ys)
   (if (== $xs ())
       ()
       (let* (($x (car-atom $xs))
              ($rest (cdr-atom $xs)))
         (if (contains? $ys $x)
             (difference2 $rest $ys)
             (let $r (difference2 $rest $ys) (cons-atom $x $r))))))

 ;; Helper function to append two expressions                                                               
 (= (append $xs $ys)                                                                                        
    (if (== $xs ())                                                                                         
        $ys                                                                                                 
        (let $r (append (cdr-atom $xs) $ys) (cons-atom (car-atom $xs) $r))))                                           
