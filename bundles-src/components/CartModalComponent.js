import React,{Component} from 'react';
import CSSTransitionGroup from 'react-transition-group/CSSTransitionGroup';
import EmptyCart from './EmptyCart';
import { Button } from 'react-bootstrap';
import {Modal} from 'react-bootstrap';
import {Table} from 'react-bootstrap';
import '../css/modal.css';

class CartModalComponent extends Component{

  constructor(props){
    super(props);
    this.state = {
      cart: this.props.cartItems
    };
  }

  render(){
    let cartItems;
    const imgStyle = {
      maxWidth: "100px",
      maxHeight: "50px"
    };
    cartItems = this.state.cart.map(product => {
      return(
        <CSSTransitionGroup transitionName="fadeIn" key={product.id} component="tr" transitionEnterTimeout={500} transitionLeaveTimeout={300}>
          <td><img src={product.image} style={imgStyle} /></td>
          <td>{product.name}</td>
          <td className="currency">{product.price}</td>
          <td>{product.quantity} шт.</td>
          <td className="currency">{product.quantity * product.price}</td>
          <td><a href="#" onClick={this.props.removeProduct.bind(this, product.id)}>×</a></td>
        </CSSTransitionGroup>
      )
    });

    let view;
    if(cartItems.length <= 0){
      view = <EmptyCart />
    } else {
      view = (
        <Table responsive>
          <thead>
            <tr>
              <th></th>
              <th>Название</th>
              <th>Цена</th>
              <th>Количество</th>
              <th>Итого</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {cartItems}
          </tbody>
        </Table>
      )
    }

    return (
      <Modal show={this.props.showCart} onHide={this.props.handleCartClose}>
        <Modal.Header closeButton>
          <center><Modal.Title>Ваша корзина</Modal.Title></center>
        </Modal.Header>
        <Modal.Body>
          {view}
        </Modal.Body>
        <Modal.Footer>
          <Button id="checkout" onClick={event => {
              document.getElementById('checkout').style.pointerEvents = 'none';
              document.getElementById("checkout").setAttribute("disabled", "disabled");
              if(this.props.cartItems.length>0){
                this.props.handleCartClose();
                this.props.handleProceed();
              }
              document.getElementById('checkout').style.pointerEvents = 'auto';
          }} className={this.props.cartItems.length>0 ? "btn btn-danger" : "disabled btn btn-danger"}>Оформить заказ</Button>
          <Button onClick={this.props.handleCartClose}>Закрыть</Button>
        </Modal.Footer>
      </Modal>
    );
  }
}

export default CartModalComponent;
