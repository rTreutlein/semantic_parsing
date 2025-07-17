;; Define Nat
(: Nat Type)
(: Z Nat)
(: S (-> Nat Nat))

;; Define cast functions between Nat and Number
(: fromNumber (-> Number Nat))
(= (fromNumber $n) (if (<= $n 0) Z (S (fromNumber (- $n 1)))))
(: fromNat (-> Nat Number))
(= (fromNat Z) 0)
(= (fromNat (S $k)) (+ 1 (fromNat $k)))

(: is-variable (-> Atom Bool))
(= (is-variable $x) (== (get-metatype $x) Variable))

(: lazy-or (-> Bool Atom Bool))
(= (lazy-or False $x) $x)
(= (lazy-or True $x) True)

(: lazy-and (-> Bool Atom Bool))
(= (lazy-and False $x) False)
(= (lazy-and True $x) $x)

(: is-expression (-> Atom Bool))
(= (is-expression $x) (== (get-metatype $x) Expression))

;Check that expression contains no variables
(: is-closed (-> Atom Bool))
(= (is-closed $x) (if (is-variable $x)
                      False
                      (if (lazy-and (is-expression $x) (not (== $x ())))
                          (lazy-and (let $head (car-atom $x) (is-closed $head))
                                    (let $tail (cdr-atom $x) (is-closed $tail)))
                          True)))



;Trace a message + argument and return the argument
(: tracem (-> Atom Atom $a))
(= (tracem $msg $a) (let $executed $a (trace! ($msg $executed) $executed)))

;Time an expression and return the result
(: mtime (-> Atom $a))
(= (mtime $expr)
   (let $start ((py-atom time.time))
   (let $res (eval (collapse $expr))
   (let $stop ((py-atom time.time))
   (Time (- $stop $start) $res)))))

(: tt (-> Atom Atom $a))
(= (tt $msg $expr)
   (tracem $msg $expr))
   ;(let $start ((py-atom time.time))
   ;(let $res (eval (collapse $expr))
   ;(let $stop ((py-atom time.time))
   ;(trace! (Time (- $stop $start) ($msg $res)) (superpose $res))))))

;;Because mettalog eliminates duplicates
(= (munion-atom $list1 $list2)
   (if-decons-expr $list1 $head $tail
      (let $res (munion-atom $tail $list2)
         (cons-atom $head $res))
      $list2))

;lambda
(: \1 (-> Atom Atom (-> Atom $r)))
(= ((\1 $var $body) $arg) (eval (sealed ($var $arg $body) (let $var $arg $body))))
(: \2 (-> Atom Atom Atom (-> Atom Atom $r)))
(= ((\2 $var1 $var2 $body) $arg1 $arg2) (eval (sealed ($var1 $var2 $arg1 $arg2 $body) (let ($var1 $var2) ($arg1 $arg2) $body))))

(= (reverse $list)
   (if-decons-expr $list $head $tail
      (let $ntail (reverse $tail)
         (munion-atom $ntail ($head)))
      ()))

!(assertEqual (reverse (a b c)) (c b a))

(= (map $list $f)
   (if-decons-expr $list $head $tail
      (let $nhead ($f $head)
      (let $ntail (map $tail $f)
         (cons-atom $nhead $ntail)))
      ()))

;; Custom fold function since the stdlib version has issues
(= (foldl $list $init $f)
   (if-decons-expr $list $head $tail
      (foldl $tail ($f $init $head) $f)
      $init))

;;Custom fold which assumes the first elment of the list as an init
(= (foldl1 $list $f)
   (if (== (get-metatype $list) Variable)
     $list
     (if-decons-expr $list $head $tail
        (foldl $tail $head $f)
        $list)))

;;Fold right to maintain the order of the list
(= (foldr $list $init $f)
   (if-decons-expr $list $head $tail
      ($f (foldr $tail $init $f) $head)
      $init))

(= (map-expr $expr $f)
   (map-atom $expr $elem (if (is-expression $elem) (map-expr $elem $f) ($f $elem))))

(= (map-expr2 $expr $f)
   ($f (map-atom $expr $elem (if (is-expression $elem) (map-expr2 $elem $f) $elem))))

(= (fold-expr $expr $init $f)
   (if-decons-expr $expr $head $tail
      (if (is-expression $head)
         (fold-expr $tail (fold-expr $head $init $f) $f)
         (fold-expr $tail ($f $init $head) $f))
      $init))


!(assertEqual (foldr (1 2 3) 0 +) 6)

;;Concat 2 sets together
;;If either set is a variable, return the other set
(= (concat $list1 $list2)
   (if (== (get-metatype $list1) Variable)
     $list2
     (if (== (get-metatype $list2) Variable)
     $list1
     (munion-atom $list1 $list2))))

!(assertEqual (concat (a b c) (a b d)) (a b c a b d))

;;Check if 3 Atoms are unifiable without modifying them
(= (=unify $a $b) (eval (sealed ($a $b) (unify $a $b True False))))

!(assertEqualAlpha (let ($v1 $v2) ($a a) ((=unify $v1 $v2) $v1 $v2)) (True $a a))

;;Remove $elem from set if it can be unified with an element in $list
;;Return the unified $elem and the remaining set
(= (remove $list $elem)
   (if-decons-expr $list $head $tail
      (unify $elem $head ($head $tail) (let ($res $ntail) (remove $tail $elem) ($res (cons-atom $head $ntail))))
      (() $list)
))

(= (removeAll $list $elem)
   (if-decons-expr $list $head $tail
      (if (=unify $elem $head)
         (removeAll $tail $elem)
         (let $ntail (removeAll $tail $elem) (cons-atom $head $ntail)))
      $list))

!(assertEqual (removeAll ((A 1) B (A 2) C) (A $a)) (B C))

;Remove $elem from $list based on unification
;If there multipel alternative return all as superposition
(= (removeAlt $list $elem)
   (if-decons-expr $list $head $tail
      (if (=unify $elem $head)
         ($head (removeAll $tail $elem))
         (let ($res $ntail) (removeAlt $tail $elem) ($res (cons-atom $head $ntail))))
      $list
))

(= (removeAlt $list $elem)
   (if-decons-expr $list $head $tail
      (if (=unify $elem $head)
        (let ($res $ntail) (removeAlt $tail $elem) ($res $ntail))
        Empty)
      Empty))

!(assertEqualToResult (removeAlt ((A 1) B (A 2) C) (A $a)) (((A 1) (B C)) ((A 2) (B C))))

!(assertEqualToResult (removeAlt ((: fact1 (A 1) (STV 0.7 0.9)) (: fact2 (A 2) (STV 0.9 0.9))) (: $prfa (A $a) $atv))
(((: fact1 (A 1) (STV 0.7 0.9)) ()) ((: fact2 (A 2) (STV 0.9 0.9)) ())))

(= (remove= $list $elem)
   (if-decons-expr $list $head $tail
      (if (== $elem $head) (remove= $tail $elem) (let $ntail (remove= $tail $elem) (cons-atom $head $ntail)))
      $list
))

(= (unique= $list)
   (if-decons-expr $list $head $tail
      (let $ntail (unique= (remove= $tail $head)) (cons-atom $head $ntail))
      $list
))

!(assertEqual (unique= ((: $a A) (: $a A) (: $b A))) ((: $a A) (: $b A)))

;;Given a proofen premise and list of target conclusions, remove the premise from the list
(= (removePrf $ccls $premise)
 (if-decons-expr $ccls $head $tail
   (if (=unify $premise $head) ;Check unifiability but don't modify the premise or the conclusion
    (let (: $prf $Type $tv) $head
     (if (lazy-or (is-closed $Type) (=alpha $premise $head)) ;If the conclusion Type is closed or the premise is alpha equivalent to the conclusion
        Empty
        ;Otherwise we need to create a superposition where we remove the conclusion and where we don't
        ;Make sure the unification of premise and conclusion happens inside the superposition to not affect the other alternative
        (let ($res $ntail) (removePrf $tail $premise) ($res (cons-atom $head $ntail)))
     ))
     ;If it is not unifiable, recurse on the tail
     Empty
  )
  ;Ccls list is empty
  Empty
 )
)

(= (removePrf $ccls $premise)
 (if-decons-expr $ccls $head $tail
   (unify $premise $head ;Check unifiability but don't modify the premise or the conclusion
     (let ($res $ntail) (removePrf $tail $premise) ((cons-atom $head $res) $ntail))
     (let ($res $ntail) (removePrf $tail $premise) ($res (cons-atom $head $ntail)))
   )
  ;Ccls list is empty
  (() $ccls)
  )
)

!(assertEqualToResult 
  (removePrf ((: $a (A $v) $tv1) (: $a2 (A $v2) $tv2)) (: a (A 1) tv3))
  ((((: a (A 1) tv3)) ((: $a (A $v) $tv1))) (() ((: $a (A $v) $tv1) (: $a2 (A $v2) $tv2))) (((: a (A 1) tv3)) ((: $a2 (A $v2) $tv2))) (((: a (A 1) tv3) (: a (A 1) tv3)) ())))

;Given a list of terms (: $prf $type $tv) and a term (: $prf2 $type2 $tv2)
;Remove all terms from the list whose $type is alpha equivlaen to $type2
(= (removeAlphaType $list $elem)
 (unify $elem (: $prf2 $type2 $tv2)
 (if-decons-expr $list $head $tail
  (unify $head (: $prf $type $tv)
   (if (and (=alpha $type $type2) (not (=unify $prf $prf2))) ;If the conclusion Type is closed or the premise is alpha equivalent to the conclusion
    (let ($res $ntail) (removeAlphaType $tail $elem) ((cons-atom $head $res) $ntail))
    (let ($res $ntail) (removeAlphaType $tail $elem) ($res (cons-atom $head $ntail)))
   )
   (let ($res $ntail) (removeAlphaType $tail $elem) ($res (cons-atom $head $ntail))))
  ;Ccls list is empty
  (() ())
 )
 (() $list)
))

!(assertEqual (removeAlphaType  ((: b (m a) tv2) (: c c tv3) (: d (m a) tv4)) (: a (m a) tv1))
  (((: b (m a) tv2) (: d (m a) tv4)) ((: c c tv3))))

;Check if an element is in a list based on unification
;Return the unified element and the remaining list
(= (elem $elem $list)
   (if-decons-expr $list $head $tail
      (unify $elem $head ($head $list) (let ($res $ntail) (elem $tail $elem) ($res (cons-atom $head $ntail))))
      (() $list)
))


!(assertEqual (elem (: $a A) ((: a $A) (: b B))) ((: a A) ((: a A) (: b B))))

;Check if $elem is a sub expression of $expr
(= (elemexpr $elem $expr)
   (if (== $elem $expr) True
     (if-decons-expr $expr $head $tail
        (if (is-expression $head)
           (elemexpr $elem $head)
           (if (== $elem $head)
              True
              (elemexpr $elem $tail)
        ))
        False
)))

!(assertEqual (elemexpr (implicat a) (traverse (implicat a))) True)
!(assertEqual (elemexpr (implicat b) (traverse (implicat a))) False)

;;Helper function for overlap
(= ((overlap_ff $rmf) ($left $intersection $right) $elem)
   (let ($res $nright) ($rmf $right $elem)
     (if (== $res ())
       ((cons-atom $elem $left) $intersection $right)
       ($left (concat $res $intersection) $nright))))

;;Calculate the overlap of 2 sets
;;Retruns (($list1 - $list2) ($list1 intersection $list2) ($list2 - $list1))
;;If the lists are  $variables don't match anything.
(= (overlap $list1 $list2)
   (if (or (is-variable $list1) (is-variable $list2))
     ($list1 () $list2)
     (foldr $list1 (() () $list2) (overlap_ff removePrf))))

!(assertEqualToResult
  (overlap ((: a2 (A 2) tv)) ((: $43991898 (A $v) $43991990)))
  ((((: a2 (A 2) tv)) () ((: $43991898 (A $v) $43991990))) (() ((: a2 (A 2) tv)) ())))

(= (overlapAlphaType $list1 $list2)
   (if (or (is-variable $list1) (is-variable $list2))
     ($list1 () $list2)
     (foldr $list1 (() () $list2) (overlap_ff removeAlphaType))))

;;Custom unique function that works with variables
(= (myunique $a) (if (is-variable $a) $a (unique= $a)))

!(assertEqual (myunique (a b a)) (a b))

;;Custom unique union function that works with variables
(= (unique-union-atom $a $b) (let $res (concat $a $b) (myunique $res)))

!(assertEqual (unique-union-atom ((: $a A) (: b B)) ((: $a A))) ((: $a A) (: b B)))
