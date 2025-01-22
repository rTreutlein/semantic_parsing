(= (traceid $x) (trace! $x $x))

;; Map function using car-atom/cdr-atom
(= (map $f $expr)
    (if (== $expr ()) ()
        (let* (($head ($f (car-atom $expr)))
               ($tail (map $f (cdr-atom $expr))))
          (cons-atom $head $tail)
        )
    )
)

;(= (double $x) (* $x 2))
;!(map double (1 2 3))

(= (fold $f $expr $init)
 (if (== $expr ()) $init
      (let* (($head ($f (car-atom $expr) $init))
             ($tail (fold $f (cdr-atom $expr) $head)))
        $tail
      )
 )
)

;!(fold + (1 2 3) 0)


(= ((replaceIn $p $t) $e)                                                                                                                                                              
     (unify $e $p $t (if (== (get-metatype $e) Expression) (map (replaceIn $p $t) $e) $e)))

(= (replaceInSpace $p $t $spaceIn $spaceOut)
     (add-atom $spaceOut (match $spaceIn $a ((replaceIn $p $t) $a)))
)

;!((replaceIn x y) x)                                                                                                                                                                   
;!((replaceIn x y) (P x))

;!(bind! &s3 (new-space))
;!(replaceInSpace x y &s1 &s3)
;!(match &s3 $a $a)


;; Function to count alpha-equivalent statements between two spaces
(= (count_alpha_equivalent $space1 $space2)
    (let* (((: $head1 $body1) (match $space1 (: $head1 $body1) (: $head1 $body1)))
           ((: $head2 $body1) (match $space2 (: $head2 $body1) (: $head2 $body1)))
           ($debug (traceid ($head2 $head1)))
           ($superpostionsum (traceid (if (== $head1 $head2) 0 1)))
           ($sum (traceid (fold + (collapse $superpostionsum) 0)))
           ($space3 (traceid (new-space)))
           ($_ (replaceInSpace $head2 $head1 $space2 $space3))
           ($out (traceid (collapse (match $space3 $a $a))))
          )
        (if (== $sum 0) (match $space1 $a (match $space2 $a $a)) (count_alpha_equivalent $space1 $space3))
    )
)

!(bind! &s1 (new-space))
!(add-atom &s1 (: x Object))
!(add-atom &s1 (: x_is_P (P x)))
!(add-atom &s1 (: z Object))
!(add-atom &s1 (: z_is_PP (PP z)))

!(bind! &s2 (new-space))
!(add-atom &s2 (: y Object))
!(add-atom &s2 (: y_is_P (P y)))
!(add-atom &s2 (: w Object))
!(add-atom &s2 (: w_is_PP (PP w)))

!(count_alpha_equivalent &s1 &s2)

