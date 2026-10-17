package
{
   import inq.hpold.battle.HpPanel;
   import inq.hpold.injector.AbstractViewInjector;
   import inq.hpold.injector.IAbstractInjector;

   public class InqHpoldPanel extends AbstractViewInjector implements IAbstractInjector
   {
      public function InqHpoldPanel()
      {
         super();
      }

      override public function get componentUI():Class
      {
         return HpPanel;
      }

      override public function get componentName():String
      {
         return "inqHpoldPanel";
      }
   }
}
