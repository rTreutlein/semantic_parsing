;; Function to count alpha-equivalent statements between two spaces
(= (count_alpha_equivalent $space1 $space2)
    (let* (((: $head1 $body1) (match $space1 (: $head1 $body1) (: $head1 $body1)))
           ((: $head2 $body1) (match $space2 (: $head2 $body1) (: $head2 $body1)))
          )
    ()
    )
)

!(bind! &s1 (new-space))
!(add-atom &s1 (: x Object))
!(add-atom &s1 (: x_is_P (P x)))

!(bind! &s2 (new-space))
!(add-atom &s2 (: y Object))
!(add-atom &s2 (: y_is_P (P y)))


!(count_alpha_equivalent &s1 &s2)

;; Map function using car-atom/cdr-atom
(= (map $f ()) ())
(= (map $f $expr)
    (let* (($head (car-atom $expr))
           ($tail (cdr-atom $expr)))
      (:: ($f $head) (map $f $tail))))

;; Test cases for map function
!(assertEqual
    (map (lambda ($x) (* $x 2)) (:: 1 (:: 2 (:: 3 ())))) 
    (:: 2 (:: 4 (:: 6 ()))))

!(assertEqual
    (map (lambda ($x) (cons-atom $x $x)) (:: "a" (:: "b" ())))
    (:: ("a" "a") (:: ("b" "b") ())))
